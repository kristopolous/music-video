import torch
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# Monkeypatch for ROCm torch: provide GroupName if missing (needed by diffusers)
try:
    import torch.distributed.distributed_c10d as c10d
    if not hasattr(c10d, "GroupName"):
        from typing import NewType
        c10d.GroupName = NewType("GroupName", str)
except Exception:
    pass

def detect_device() -> str:
    if torch.cuda.is_available():
        is_rocm = (
            hasattr(torch.version, "hip")
            and torch.version.hip is not None
        )
        if is_rocm:
            logger.info(f"ROCm device detected (HIP {torch.version.hip})")
        else:
            cuda_ver = torch.version.cuda or "unknown"
            logger.info(f"CUDA device detected (CUDA {cuda_ver})")
        return "cuda"
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        logger.info("Intel XPU device detected")
        return "xpu"
    logger.warning("No GPU detected — falling back to CPU")
    return "cpu"

class ModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.models = {}
        return cls._instance

    async def get_qwen(self, prefer_transformers: bool = False):
        if "qwen" not in self.models:
            from huggingface_hub import hf_hub_download

            is_rocm = (
                hasattr(torch.version, "hip")
                and torch.version.hip is not None
            )
            device = detect_device()
            use_gpu = device == "cuda"

            path = await asyncio.to_thread(
                hf_hub_download,
                repo_id="unsloth/Qwen3.6-35B-A3B-GGUF",
                filename="Qwen3.6-35B-A3B-UD-Q4_K_S.gguf",
                local_dir="models"
            )
            logger.info(f"Loading Qwen3.6 GGUF from {path} on device: {device}")

            if use_gpu and not prefer_transformers:
                try:
                    self.models["qwen"] = await self._load_llama_cpp_gpu(path, is_rocm)
                except Exception as e:
                    logger.warning(f"llama-cpp GPU load failed: {e}, falling back to transformers")
                    self.models["qwen"] = await self.get_qwen_transformers()
            elif use_gpu and prefer_transformers:
                self.models["qwen"] = await self.get_qwen_transformers()
            else:
                self.models["qwen"] = await self._load_llama_cpp_cpu(path)
                logger.warning("Qwen loaded on CPU - inference will be slow")

        return self.models["qwen"]

    async def _load_llama_cpp_gpu(self, path: str, is_rocm: bool):
        from llama_cpp import Llama
        import asyncio

        def _load():
            llama_params = {
                "model_path": path,
                "n_gpu_layers": -1,
                "n_ctx": 32768,
                "verbose": False,
            }

            if is_rocm:
                llama_params["main_gpu"] = 0
                llama_params["tensor_split"] = None
                llama_params["use_mmap"] = True
                llama_params["use_mlock"] = False
                logger.info("Configuring llama-cpp for AMD ROCm GPU inference")

            llm = Llama(**llama_params)

            gpu_layers = getattr(llm, "n_gpu_layers", -1) if hasattr(llm, "n_gpu_layers") else -1
            if hasattr(llm, "model") and hasattr(llm.model, "n_tokens"):
                logger.info(f"llama-cpp loaded with n_gpu_layers={gpu_layers}")
            logger.info(f"Qwen GGUF ready on {'ROCm' if is_rocm else 'CUDA'} GPU")

            return llm

        return await asyncio.to_thread(_load)

    async def _load_llama_cpp_cpu(self, path: str):
        from llama_cpp import Llama
        import asyncio

        def _load():
            return Llama(
                model_path=path,
                n_gpu_layers=0,
                n_ctx=32768,
                verbose=False,
            )

        return await asyncio.to_thread(_load)

    async def get_qwen_transformers(self):
        if "qwen_transformers" not in self.models:
            logger.info("Loading Qwen3.6-35B via transformers on GPU...")
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import asyncio

            device = detect_device()
            dtype = torch.bfloat16 if device == "cuda" else torch.float32

            def _load():
                tokenizer = AutoTokenizer.from_pretrained(
                    "Qwen/Qwen3-35B",
                    trust_remote_code=True
                )
                model = AutoModelForCausalLM.from_pretrained(
                    "Qwen/Qwen3-35B",
                    torch_dtype=dtype,
                    device_map="auto",
                    trust_remote_code=True
                )
                return model, tokenizer

            model, tokenizer = await asyncio.to_thread(_load)
            self.models["qwen_transformers"] = (model, tokenizer)
            logger.info(f"Qwen transformers ready on {device}")

        return self.models["qwen_transformers"]

    async def get_asr(self):
        if "asr" not in self.models:
            logger.info("Loading Qwen3-ASR-1.7B...")
            from qwen_asr import Qwen3ASRModel
            import asyncio
            self.models["asr"] = await asyncio.to_thread(
                Qwen3ASRModel.from_pretrained,
                "Qwen/Qwen3-ASR-1.7B",
                dtype=torch.bfloat16,
                device_map="auto"
            )
        return self.models["asr"]

    async def get_forced_aligner(self):
        if "forced_aligner" not in self.models:
            logger.info("Loading Qwen3-ForcedAligner-0.6B...")
            from qwen_asr.inference import Qwen3ForcedAligner
            import asyncio
            self.models["forced_aligner"] = await asyncio.to_thread(
                Qwen3ForcedAligner.from_pretrained,
                "Qwen/Qwen3-ForcedAligner-0.6B",
                dtype=torch.bfloat16,
                device_map="auto"
            )
        return self.models["forced_aligner"]

    async def get_ltx(self):
        if "ltx" not in self.models:
            logger.info("Loading LTX-2.3 GGUF via Diffusers...")
            from diffusers import LTX2Pipeline
            import asyncio
            pipe = await asyncio.to_thread(
                LTX2Pipeline.from_pretrained,
                "Lightricks/LTX-2.3",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True
            )
            pipe.to(detect_device())
            self.models["ltx"] = pipe
        return self.models["ltx"]

    async def get_ace_step_pipeline(self):
        """Initialize and return (dit_handler, llm_handler) for ACE-Step."""
        if "ace_step" not in self.models:
            logger.info("Initializing ACE-Step pipeline...")
            from acestep.handler import AceStepHandler
            from acestep.llm_inference import LLMHandler
            from acestep.gpu_config import get_gpu_config, set_global_gpu_config
            from acestep.model_downloader import ensure_lm_model
            import asyncio

            gpu_config = get_gpu_config()
            set_global_gpu_config(gpu_config)

            dit_handler = AceStepHandler()
            llm_handler = LLMHandler()

            project_root = os.path.abspath("ACE-Step-1.5")

            def _init_dit():
                status, ok = dit_handler.initialize_service(
                    project_root=project_root,
                    config_path="acestep-v15-turbo",
                    device=detect_device(),
                    offload_to_cpu=gpu_config.gpu_memory_gb < 16,
                )
                if not ok:
                    raise RuntimeError(f"DiT init failed: {status}")
                return status

            logger.info("Initializing DiT model...")
            await asyncio.to_thread(_init_dit)
            logger.info("DiT model ready.")

            if gpu_config.init_lm_default:
                checkpoint_dir = os.path.join(project_root, "checkpoints")

                async def _ensure_lm():
                    ok, msg = await asyncio.to_thread(
                        ensure_lm_model,
                        model_name="acestep-5Hz-lm-1.7B",
                        checkpoints_dir=checkpoint_dir,
                    )
                    if not ok:
                        logger.warning(f"LM download: {msg}")

                await _ensure_lm()

                def _init_lm():
                    status, ok = llm_handler.initialize(
                        checkpoint_dir=checkpoint_dir,
                        lm_model_path="acestep-5Hz-lm-1.7B",
                        backend=gpu_config.recommended_backend,
                        device=detect_device(),
                        offload_to_cpu=gpu_config.gpu_memory_gb < 16,
                    )
                    if not ok:
                        raise RuntimeError(f"LM init failed: {status}")
                    return status

                logger.info("Initializing LM...")
                try:
                    await asyncio.to_thread(_init_lm)
                    logger.info("LM ready.")
                except Exception as e:
                    logger.warning(f"LM init skipped: {e}")

            self.models["ace_step"] = (dit_handler, llm_handler)
        return self.models["ace_step"]

model_manager = ModelManager()
