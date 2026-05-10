from app.core.steps.base import BaseStep
from app.core.model_manager import model_manager
import asyncio
import re
from dataclasses import dataclass
from typing import List

@dataclass
class TimestampItem:
    text: str
    start: float
    end: float

def detect_language(text: str) -> str:
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(re.findall(r'[^\s\d\W_]', text))
    
    if total_chars > 0 and chinese_chars / total_chars > 0.3:
        return "Chinese"
    
    japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
    if total_chars > 0 and japanese_chars / total_chars > 0.3:
        return "Japanese"
    
    korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
    if total_chars > 0 and korean_chars / total_chars > 0.3:
        return "Korean"
    
    return "English"

class ExtractTimestampsStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        song_path = context.get("song_path")
        lyrics = context.get("lyrics", "")
        
        await self.update_progress(project_id, "Extracting timestamps with Qwen3-ForcedAligner...", 0.1)
        
        def extract(aligner):
            language = detect_language(lyrics) if lyrics else "English"
            
            results = aligner.align(
                audio=song_path,
                text=lyrics,
                language=language
            )
            
            timestamp_items: List[TimestampItem] = []
            if results and len(results) > 0:
                for item in results[0]:
                    timestamp_items.append(TimestampItem(
                        text=item.text,
                        start=item.start_time,
                        end=item.end_time
                    ))
            
            return timestamp_items

        aligner = await model_manager.get_forced_aligner()
        timestamps = await asyncio.to_thread(extract, aligner)
        
        context["lyrics_with_timestamps"] = timestamps
        await self.update_progress(project_id, f"Timestamps extracted ({len(timestamps)} items).", 1.0)
        return timestamps
