import torch
import logging
import os
import httpx
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import asyncio

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.models = {}
            cls._instance.paths = {
                "qwen": None,
                "acestep": None,
                "ltx": None
            }
        return cls._instance

    async def download_model(self, repo_id, filename, key):
        if self.paths[key] and os.path.exists(self.paths[key]):
            return self.paths[key]
        
        logger.info(f"Downloading {filename} from {repo_id}...")
        path = await asyncio.to_thread(
            hf_hub_download,
            repo_id=repo_id,
            filename=filename,
            local_dir="models"
        )
        self.paths[key] = path
        logger.info(f"Downloaded to {path}")
        return path

    async def get_qwen(self):
        if "qwen" not in self.models:
            path = await self.download_model(
                repo_id="unsloth/Qwen3.6-35B-A3B-GGUF",
                filename="Qwen3.6-35B-A3B-UD-Q4_K_S.gguf",
                key="qwen"
            )
            logger.info(f"Loading Qwen3.6 GGUF from {path}...")
            self.models["qwen"] = Llama(
                model_path=path,
                n_gpu_layers=-1,
                n_ctx=4096,
                verbose=False
            )
        return self.models["qwen"]

    async def get_acestep(self):
        if "acestep" not in self.models:
            # ACE-Step has multiple components in GGUF. We'll download the main LM for now.
            # In a full implementation, we'd need the DiT part too for synthesis.
            path = await self.download_model(
                repo_id="Serveurperso/ACE-Step-1.5-GGUF",
                filename="acestep-5Hz-lm-4B-Q8_0.gguf",
                key="acestep"
            )
            logger.info(f"Loading ACE-Step GGUF from {path}...")
            self.models["acestep"] = Llama(
                model_path=path,
                n_gpu_layers=-1,
                verbose=False
            )
        return self.models["acestep"]

    async def get_asr(self):
        if "asr" not in self.models:
            logger.info("Loading Qwen3-ASR-1.7B...")
            from qwen_asr import Qwen3ASRModel
            self.models["asr"] = await asyncio.to_thread(
                Qwen3ASRModel.from_pretrained,
                "Qwen/Qwen3-ASR-1.7B",
                dtype=torch.bfloat16,
                device_map="auto"
            )
        return self.models["asr"]

    async def get_ltx(self):
        if "ltx" not in self.models:
            # Unsloth LTX-2.3-GGUF with Diffusers LTX2Pipeline support
            logger.info("Loading LTX-2.3 GGUF via Diffusers...")
            from diffusers import LTX2Pipeline
            # Note: We need the GGUF weights to be compatible with LTX2Pipeline.
            # In a real environment, you might use a specific GGUF-compatible loader 
            # or the unsloth optimized version.
            pipe = await asyncio.to_thread(
                LTX2Pipeline.from_pretrained,
                "Lightricks/LTX-2.3",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True
            )
            pipe.to("cuda")
            self.models["ltx"] = pipe
        return self.models["ltx"]

model_manager = ModelManager()
