import os
import json
from typing import List, Dict, Any, Optional
try:
    from openai import OpenAI
except ImportError:  # 允许在未安装 openai 的环境下离线运行
    OpenAI = None

from datetime import datetime

from app.config import settings



class AIService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY and OpenAI is not None:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.whisper_model = settings.WHISPER_MODEL

    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        if not self.client:
            return {
                "raw_text": "",
                "segments": [],
                "language": "zh"
            }

        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    language="zh"
                )

            return {
                "raw_text": transcription.text,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                        "speaker": None
                    }
                    for seg in transcription.segments
                ] if hasattr(transcription, 'segments') else [],
                "language": getattr(transcription, 'language', 'zh')
            }
        except Exception as e:
            print(f"Transcription error: {e}")
            return {
                "raw_text": "",
                "segments": [],
                "language": "zh"
            }

    async def diarize_audio(self, audio_path: str) -> Dict[str, Any]:
        if not settings.PYANNOTE_AUTH_TOKEN:
            return {
                "speakers": [],
                "segments": []
            }

        try:
            from pyannote.audio import Pipeline
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=settings.PYANNOTE_AUTH_TOKEN
            )

            import torchaudio
            waveform, sample_rate = torchaudio.load(audio_path)
            diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})

            segments = []
            speakers = set()

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
                speakers.add(speaker)

            return {
                "speakers": list(speakers),
                "segments": segments
            }
        except Exception as e:
            print(f"Diarization error: {e}")
            return {
                "speakers": [],
                "segments": []
            }

    async def merge_transcript_and_diarization(
        self,
        transcript_data: Dict[str, Any],
        diarization_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        merged_segments = []

        for trans_segment in transcript_data.get("segments", []):
            trans_start = trans_segment["start"]
            trans_end = trans_segment["end"]
            trans_text = trans_segment["text"]

            best_speaker = None
            max_overlap = 0

            for diar_segment in diarization_data.get("segments", []):
                diar_start = diar_segment["start"]
                diar_end = diar_segment["end"]

                overlap_start = max(trans_start, diar_start)
                overlap_end = min(trans_end, diar_end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = diar_segment["speaker"]

            merged_segments.append({
                "start": trans_start,
                "end": trans_end,
                "text": trans_text,
                "speaker": best_speaker
            })

        return merged_segments

    async def classify_speaker_roles(
        self,
        merged_segments: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        if not self.client:
            return {}

        speaker_texts = {}
        for seg in merged_segments:
            speaker = seg.get("speaker", "unknown")
            if speaker not in speaker_texts:
                speaker_texts[speaker] = []
            speaker_texts[speaker].append(seg["text"])

        roles = {}
        for speaker, texts in speaker_texts.items():
            combined_text = " ".join(texts[:10])

            prompt = f"""
            请根据以下说话内容判断说话者的角色是"农人"还是"消费者"。
            农人通常讨论种植、蔬菜生长、农场管理等话题。
            消费者通常讨论口味偏好、配送问题、食谱、购买需求等话题。

            说话内容: {combined_text}

            请只返回"农人"或"消费者"，不要返回其他内容。
            """

            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10
                )
                role = response.choices[0].message.content.strip()
                roles[speaker] = role if role in ["农人", "消费者"] else "unknown"
            except Exception as e:
                print(f"Role classification error: {e}")
                roles[speaker] = "unknown"

        return roles

    async def extract_preferences_and_feedback(
        self,
        processed_transcript: List[Dict[str, Any]],
        speaker_roles: Dict[str, str]
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "taste_preferences": [],
                "delivery_feedback": [],
                "quality_feedback": [],
                "suggestions": []
            }

        consumer_texts = []
        for seg in processed_transcript:
            speaker = seg.get("speaker")
            if speaker and speaker_roles.get(speaker) == "消费者":
                consumer_texts.append(seg["text"])

        all_text = " ".join(consumer_texts)

        function_schema = {
            "name": "extract_csa_feedback",
            "parameters": {
                "type": "object",
                "properties": {
                    "taste_preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "消费者提到的口味偏好，如喜欢的蔬菜、不喜欢的口味等"
                    },
                    "delivery_feedback": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关于配送时间、方式、包装等的反馈"
                    },
                    "quality_feedback": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关于蔬菜品质、新鲜度等的反馈"
                    },
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "消费者的其他建议和需求"
                    }
                },
                "required": ["taste_preferences", "delivery_feedback", "quality_feedback", "suggestions"]
            }
        }

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个CSA社区支持农业的数据分析助手，请从对话中提取消费者的偏好和反馈。"},
                    {"role": "user", "content": f"以下是消费者的发言内容，请提取相关信息：\n\n{all_text}"}
                ],
                functions=[function_schema],
                function_call={"name": "extract_csa_feedback"}
            )

            function_call = response.choices[0].message.function_call
            if function_call:
                return json.loads(function_call.arguments)
        except Exception as e:
            print(f"Extraction error: {e}")

        return {
            "taste_preferences": [],
            "delivery_feedback": [],
            "quality_feedback": [],
            "suggestions": []
        }

    async def generate_planting_intent(
        self,
        all_feedback: List[Dict[str, Any]],
        current_vegetables: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "next_season_vegetables": [],
                "share_adjustments": {},
                "member_preferences": {},
                "recommendations": []
            }

        feedback_text = json.dumps(all_feedback, ensure_ascii=False, indent=2)
        vegetables_text = json.dumps(current_vegetables, ensure_ascii=False, indent=2)

        function_schema = {
            "name": "generate_planting_plan",
            "parameters": {
                "type": "object",
                "properties": {
                    "next_season_vegetables": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "planting_area": {"type": "number"},
                                "expected_yield": {"type": "number"},
                                "priority": {"type": "string", "enum": ["高", "中", "低"]}
                            },
                            "required": ["name", "planting_area", "expected_yield", "priority"]
                        }
                    },
                    "share_adjustments": {
                        "type": "object",
                        "description": "各蔬菜份额的调整建议，如增加或减少的百分比"
                    },
                    "member_preferences": {
                        "type": "object",
                        "properties": {
                            "most_popular": {"type": "array", "items": {"type": "string"}},
                            "least_popular": {"type": "array", "items": {"type": "string"}},
                            "common_requests": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "针对下一季的具体建议"
                    }
                },
                "required": ["next_season_vegetables", "share_adjustments", "member_preferences", "recommendations"]
            }
        }

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个CSA社区支持农业的农业规划专家，请根据会员反馈和当前种植情况生成下一季的种植计划。"},
                    {"role": "user", "content": f"当前蔬菜品种：\n{vegetables_text}\n\n会员反馈汇总：\n{feedback_text}"}
                ],
                functions=[function_schema],
                function_call={"name": "generate_planting_plan"}
            )

            function_call = response.choices[0].message.function_call
            if function_call:
                return json.loads(function_call.arguments)
        except Exception as e:
            print(f"Planting intent generation error: {e}")

        return {
            "next_season_vegetables": [],
            "share_adjustments": {},
            "member_preferences": {},
            "recommendations": []
        }

    async def generate_recipes(
        self,
        vegetables: List[str],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        vegetables_text = ", ".join(vegetables)

        function_schema = {
            "name": "generate_recipes",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "vegetables_used": {"type": "array", "items": {"type": "string"}},
                                "ingredients": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "quantity": {"type": "string"}
                                        },
                                        "required": ["name", "quantity"]
                                    }
                                },
                                "steps": {"type": "array", "items": {"type": "string"}},
                                "cooking_time": {"type": "integer"},
                                "difficulty": {"type": "string", "enum": ["简单", "中等", "困难"]}
                            },
                            "required": ["title", "vegetables_used", "ingredients", "steps", "cooking_time", "difficulty"]
                        }
                    }
                },
                "required": ["recipes"]
            }
        }

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的营养师和厨师，请为CSA会员设计健康美味的时令蔬菜食谱。"},
                    {"role": "user", "content": f"请使用以下时令蔬菜设计{count}道菜谱：{vegetables_text}"}
                ],
                functions=[function_schema],
                function_call={"name": "generate_recipes"}
            )

            function_call = response.choices[0].message.function_call
            if function_call:
                result = json.loads(function_call.arguments)
                return result.get("recipes", [])
        except Exception as e:
            print(f"Recipe generation error: {e}")

        return []

    async def generate_meeting_summary(
        self,
        conversation_messages: List[Dict[str, Any]],
        speaker_roles: Dict[str, str]
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "summary": "",
                "key_decisions": [],
                "action_items": [],
                "next_steps": []
            }

        messages_text = "\n".join([
            f"[{msg.get('sender_role', '未知')}] {msg.get('content', '')}"
            for msg in conversation_messages
        ])

        function_schema = {
            "name": "generate_meeting_summary",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "会议内容的简要总结"},
                    "key_decisions": {"type": "array", "items": {"type": "string"}, "description": "会议中的重要决定"},
                    "action_items": {"type": "array", "items": {"type": "string"}, "description": "需要执行的事项"},
                    "next_steps": {"type": "array", "items": {"type": "string"}, "description": "下一步计划"}
                },
                "required": ["summary", "key_decisions", "action_items", "next_steps"]
            }
        }

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的会议记录员，请为CSA会员大会生成会议纪要。"},
                    {"role": "user", "content": f"以下是会议对话内容：\n\n{messages_text}"}
                ],
                functions=[function_schema],
                function_call={"name": "generate_meeting_summary"}
            )

            function_call = response.choices[0].message.function_call
            if function_call:
                return json.loads(function_call.arguments)
        except Exception as e:
            print(f"Meeting summary error: {e}")

        return {
            "summary": "",
            "key_decisions": [],
            "action_items": [],
            "next_steps": []
        }


ai_service = AIService()


