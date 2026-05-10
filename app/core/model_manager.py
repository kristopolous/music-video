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

    async def get_qwen(self):
        if "qwen" not in self.models:
            from llama_cpp import Llama
            from huggingface_hub import hf_hub_download
            import asyncio

            def _download():
                return hf_hub_download(
                    repo_id="unsloth/Qwen3.6-35B-A3B-GGUF",
                    filename="Qwen3.6-35B-A3B-UD-Q4_K_S.gguf",
                    local_dir="models"
                )

            def _load(path):
                is_rocm = (
                    hasattr(torch.version, "hip")
                    and torch.version.hip is not None
                )
                
                llama_params = {
                    "model_path": path,
                    "n_gpu_layers": -1,
                    "n_ctx": 32768,
                    "verbose": False,
                }
                
                if is_rocm:
                    llama_params["n_gpu_layers"] = -1
                    llama_params["main_gpu"] = 0
                    llama_params["tensor_split"] = None
                    logger.info("Configuring llama-cpp for AMD ROCm GPU inference")
                
                return Llama(**llama_params)

            path = await asyncio.to_thread(_download)
            logger.info(f"Loading Qwen3.6 GGUF from {path}...")
            self.models["qwen"] = await asyncio.to_thread(_load, path)
        return self.models["qwen"]

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
