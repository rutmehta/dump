from google import genai
from google.genai import types
import logging
import asyncio
import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re
from PIL import Image
import assemblyai as aai
from ..config import settings

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.client = None
        self.assembly_client = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Gemini Gen AI client and AssemblyAI services"""
        try:
            # Initialize new Gemini Gen AI client
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Initialize AssemblyAI for audio processing
            if settings.ASSEMBLYAI_API_KEY:
                aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
                self.assembly_client = aai.Transcriber()
            
            self.system_prompt = """
            You are LifeOS - an autonomous AI assistant that operates as a comprehensive life management system. 
            
            Your core capabilities:
            1. Process multimodal inputs (text, images, audio, documents, video) with deep understanding
            2. Maintain long-term memory and context across conversations with up to 2M token context window
            3. Proactively surface relevant information without explicit queries
            4. Extract and map relationships between concepts, entities, and events
            5. Provide context-aware responses based on user's history and preferences
            6. Handle complex reasoning across multiple modalities simultaneously
            
            Key behaviors:
            - Always consider the user's historical context and established patterns
            - Identify and extract entities, concepts, and relationships from all inputs
            - Provide insights that connect current inputs to past conversations
            - Be proactive in offering relevant information and suggestions
            - Maintain awareness of temporal context and evolving situations
            - Extract sentiment and emotional context from interactions
            - Analyze visual, audio, and textual content comprehensively
            
            Response format:
            - Primary response addressing the user's immediate need
            - Context connections to previous conversations when relevant
            - Extracted metadata for memory storage (entities, concepts, sentiment)
            - Proactive suggestions based on patterns and context
            """
            
            logger.info("New Gemini Gen AI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}")
            raise
    
    async def process_input(self, 
                           text: Optional[str] = None,
                           media_path: Optional[str] = None,
                           media_type: str = "text",
                           user_id: str = "",
                           context_memories: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process multimodal input and generate contextual response using new Gen AI SDK"""
        
        try:
            # Prepare input content using new SDK format
            contents = []
            
            # Add context from memories as text content
            if context_memories:
                context_text = self._format_context_memories(context_memories)
                contents.append(f"PREVIOUS CONTEXT:\n{context_text}")
            
            # Add current text input
            if text:
                contents.append(f"CURRENT INPUT: {text}")
            
            # Handle media input with enhanced multimodal support
            if media_path and os.path.exists(media_path):
                if media_type == "image":
                    # Use new SDK's native image support
                    contents.append(types.Part.from_image(path=media_path))
                elif media_type == "audio":
                    # Use new SDK's native audio support or fallback to transcription
                    try:
                        contents.append(types.Part.from_audio(path=media_path))
                    except:
                        # Fallback to transcription if direct audio processing fails
                        transcription = await self._transcribe_audio(media_path)
                        contents.append(f"AUDIO TRANSCRIPTION: {transcription}")
                        text = transcription
                elif media_type == "document":
                    # Extract text from document
                    doc_text = await self._extract_document_text(media_path)
                    contents.append(f"DOCUMENT CONTENT: {doc_text}")
                    text = doc_text
                elif media_type == "video":
                    # Use new SDK's video understanding capabilities
                    try:
                        contents.append(types.Part.from_video(path=media_path))
                    except:
                        # Fallback if video processing is not available
                        contents.append(f"VIDEO FILE: {media_path} (processing not available)")
            
            # Add processing instructions
            contents.append("""
            Please process this input and provide:
            1. A natural, helpful response to the user
            2. Extracted entities and concepts
            3. Sentiment analysis
            4. Relationship mappings to previous context
            5. Proactive insights or suggestions
            
            Format your response as JSON with these fields:
            {
                "response": "Your main response to the user",
                "entities": ["list", "of", "extracted", "entities"],
                "concepts": ["list", "of", "key", "concepts"],
                "sentiment": "positive/negative/neutral",
                "keywords": ["relevant", "keywords"],
                "relationships": [{"concept1": "A", "concept2": "B", "strength": 0.8}],
                "insights": ["proactive insights based on context"],
                "metadata": {"any": "additional", "structured": "data"}
            }
            """)
            
            # Generate response using new Gen AI SDK with enhanced capabilities
            config = types.GenerateContentConfig(
                max_output_tokens=settings.MAX_OUTPUT_TOKENS,
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P,
                # Enable long context processing
                system_instruction=self.system_prompt
            )
            
            response = await self._generate_with_retry(contents, config)
            
            # Parse and structure the response
            structured_response = self._parse_ai_response(response.text)
            
            # Add processing metadata
            structured_response.update({
                "input_type": media_type,
                "processing_time": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "original_text": text or "",
                "media_path": media_path,
                "context_length": len(str(contents)),
                "model_used": "gemini-2.0-flash-exp"
            })
            
            logger.info(f"Processed {media_type} input for user {user_id} with new Gen AI SDK")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to process input with new SDK: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "entities": [],
                "concepts": [],
                "sentiment": "neutral",
                "keywords": [],
                "relationships": [],
                "insights": [],
                "metadata": {"error": str(e), "sdk_version": "new_genai"}
            }
    
    async def _generate_with_retry(self, contents: List, config: types.GenerateContentConfig, max_retries: int = 3):
        """Generate response with retry logic using new SDK"""
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _format_context_memories(self, memories: List[Dict]) -> str:
        """Format context memories for inclusion in prompt with enhanced context handling"""
        context_lines = []
        # With 2M token context window, we can include more memories
        for memory in memories[:25]:  # Increased from 10 to 25 due to larger context window
            timestamp = memory.get('timestamp', 'unknown')
            content = memory.get('content', '')
            content_type = memory.get('content_type', 'text')
            entities = memory.get('entities', [])
            sentiment = memory.get('sentiment', 'neutral')
            
            # Enhanced context formatting with more metadata
            entities_str = ', '.join(entities[:5]) if entities else 'none'
            context_lines.append(
                f"[{timestamp}] ({content_type}) [{sentiment}] Entities: {entities_str} | {content[:300]}..."
            )
        
        return "\n".join(context_lines)
    
    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using AssemblyAI with enhanced features"""
        try:
            if not self.assembly_client:
                return "Audio transcription not available - AssemblyAI key not configured"
            
            # Enhanced transcription configuration
            config = aai.TranscriptionConfig(
                speaker_labels=True,
                auto_highlights=True,
                sentiment_analysis=True,
                entity_detection=True,
                iab_categories=True,
                content_safety=True
            )
            
            transcript = self.assembly_client.transcribe(audio_path, config)
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription failed: {transcript.error}")
                return "Failed to transcribe audio"
            
            # Enhanced formatting with metadata
            result_parts = []
            
            # Add basic transcription
            if transcript.utterances:
                formatted_text = []
                for utterance in transcript.utterances:
                    speaker = f"Speaker {utterance.speaker}"
                    text = utterance.text
                    confidence = f"(confidence: {utterance.confidence:.2f})"
                    formatted_text.append(f"{speaker}: {text} {confidence}")
                result_parts.append("TRANSCRIPTION:\n" + "\n".join(formatted_text))
            else:
                result_parts.append(f"TRANSCRIPTION: {transcript.text}")
            
            # Add sentiment analysis
            if hasattr(transcript, 'sentiment_analysis_results') and transcript.sentiment_analysis_results:
                sentiments = [f"{s.text}: {s.sentiment}" for s in transcript.sentiment_analysis_results[:3]]
                result_parts.append(f"SENTIMENT: {', '.join(sentiments)}")
            
            # Add auto highlights
            if hasattr(transcript, 'auto_highlights') and transcript.auto_highlights:
                highlights = [h.text for h in transcript.auto_highlights.results[:5]]
                result_parts.append(f"KEY POINTS: {', '.join(highlights)}")
            
            return "\n\n".join(result_parts)
                
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return "Audio transcription failed"
    
    async def _extract_document_text(self, doc_path: str) -> str:
        """Extract text from document files using new SDK capabilities"""
        try:
            # Simple text extraction for basic files
            if doc_path.lower().endswith('.txt'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Use new SDK's enhanced document processing
                try:
                    # Try using new SDK's document understanding
                    response = self.client.models.generate_content(
                        model='gemini-2.0-flash-exp',
                        contents=[
                            "Extract and analyze the key content from this document. Provide a comprehensive summary with main points, entities, and key information:",
                            types.Part.from_image(path=doc_path)  # Many docs can be processed as images
                        ]
                    )
                    return response.text
                except:
                    # Fallback to basic file reading
                    with open(doc_path, 'rb') as f:
                        content = f.read()
                        # Try to decode as text
                        try:
                            return content.decode('utf-8')
                        except:
                            return f"Binary document file: {os.path.basename(doc_path)} ({len(content)} bytes)"
                
        except Exception as e:
            logger.error(f"Document text extraction failed: {e}")
            return "Failed to extract document text"
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data with enhanced error handling"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                # Validate required fields and add defaults if missing
                required_fields = {
                    "response": response_text,
                    "entities": [],
                    "concepts": [],
                    "sentiment": "neutral",
                    "keywords": [],
                    "relationships": [],
                    "insights": [],
                    "metadata": {}
                }
                
                for field, default in required_fields.items():
                    if field not in parsed:
                        parsed[field] = default
                
                return parsed
            else:
                # Fallback parsing if JSON format is not found
                return {
                    "response": response_text,
                    "entities": self._extract_entities_fallback(response_text),
                    "concepts": self._extract_concepts_fallback(response_text),
                    "sentiment": self._analyze_sentiment_fallback(response_text),
                    "keywords": self._extract_keywords_fallback(response_text),
                    "relationships": [],
                    "insights": [],
                    "metadata": {"parsing_method": "fallback"}
                }
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse structured AI response, using enhanced fallback")
            return {
                "response": response_text,
                "entities": self._extract_entities_fallback(response_text),
                "concepts": self._extract_concepts_fallback(response_text),
                "sentiment": self._analyze_sentiment_fallback(response_text),
                "keywords": self._extract_keywords_fallback(response_text),
                "relationships": [],
                "insights": [],
                "metadata": {"parsing_method": "enhanced_fallback"}
            }
    
    def _extract_entities_fallback(self, text: str) -> List[str]:
        """Enhanced fallback entity extraction using improved patterns"""
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',  # Days
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',  # Months
            r'\b\d{1,2}:\d{2}(?:\s*[APap][Mm])?\b',  # Times
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Dates
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\$\d+(?:\.\d{2})?\b',  # Money amounts
        ]
        
        entities = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)
        
        # Remove common false positives
        false_positives = {'The', 'This', 'That', 'They', 'There', 'Then', 'When', 'Where', 'What', 'Who', 'Why', 'How'}
        entities = entities - false_positives
        
        return list(entities)[:25]  # Increased limit for better context
    
    def _extract_concepts_fallback(self, text: str) -> List[str]:
        """Enhanced fallback concept extraction"""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Enhanced stop words list
        stop_words = {
            'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 
            'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 
            'other', 'after', 'first', 'well', 'water', 'very', 'what', 'know',
            'just', 'back', 'good', 'much', 'before', 'right', 'through', 'when',
            'where', 'should', 'those', 'these', 'being', 'both', 'more', 'most'
        }
        
        from collections import Counter
        word_freq = Counter(word for word in words if word not in stop_words)
        return [word for word, freq in word_freq.most_common(15) if freq > 1]
    
    def _analyze_sentiment_fallback(self, text: str) -> str:
        """Enhanced fallback sentiment analysis"""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'happy', 'love',
            'fantastic', 'awesome', 'brilliant', 'perfect', 'outstanding', 'superb',
            'delighted', 'thrilled', 'excited', 'pleased', 'satisfied', 'enjoy'
        ]
        negative_words = [
            'bad', 'terrible', 'awful', 'hate', 'sad', 'angry', 'frustrated',
            'horrible', 'disgusting', 'disappointed', 'upset', 'annoyed', 'worried',
            'concerned', 'stressed', 'anxious', 'depressed', 'miserable', 'furious'
        ]
        
        text_lower = text.lower()
        positive_count = sum(2 if word in text_lower else 0 for word in positive_words)
        negative_count = sum(2 if word in text_lower else 0 for word in negative_words)
        
        # Consider intensity modifiers
        intensifiers = ['very', 'extremely', 'really', 'absolutely', 'completely']
        for intensifier in intensifiers:
            if intensifier in text_lower:
                positive_count *= 1.2
                negative_count *= 1.2
        
        if positive_count > negative_count * 1.2:
            return "positive"
        elif negative_count > positive_count * 1.2:
            return "negative"
        else:
            return "neutral"
    
    def _extract_keywords_fallback(self, text: str) -> List[str]:
        """Enhanced fallback keyword extraction"""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        from collections import Counter
        word_freq = Counter(words)
        
        # Enhanced stop words
        stop_words = {
            'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 
            'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 
            'other', 'after', 'first', 'well', 'water', 'very', 'what', 'know',
            'just', 'back', 'good', 'much', 'before', 'right', 'through', 'when',
            'where', 'should', 'those', 'these', 'being', 'both', 'more', 'most',
            'some', 'such', 'only', 'also', 'even', 'come', 'make', 'take'
        }
        
        keywords = [word for word, freq in word_freq.most_common(20) if word not in stop_words and freq > 1]
        return keywords[:12]
    
    async def generate_metadata(self, content: str, content_type: str) -> Dict[str, Any]:
        """Generate enhanced metadata for content using new Gen AI SDK"""
        try:
            contents = [
                f"Analyze this {content_type} content and extract comprehensive metadata:",
                content[:2000],  # Increased content length for better analysis
                """
                Provide a JSON response with:
                {
                    "summary": "Brief but comprehensive summary of the content",
                    "topics": ["list", "of", "main", "topics"],
                    "entities": ["extracted", "entities", "including", "people", "places", "organizations"],
                    "sentiment": "positive/negative/neutral",
                    "keywords": ["key", "words", "and", "phrases"],
                    "urgency": "low/medium/high",
                    "category": "personal/work/health/finance/education/entertainment/travel/technology/etc",
                    "emotional_tone": "calm/excited/concerned/happy/sad/angry/neutral",
                    "action_items": ["any", "action", "items", "or", "tasks", "mentioned"],
                    "temporal_references": ["dates", "times", "deadlines", "mentioned"]
                }
                """
            ]
            
            config = types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.1,  # Lower temperature for more consistent metadata extraction
                top_p=0.9
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=contents,
                config=config
            )
            
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            logger.error(f"Failed to generate metadata with new SDK: {e}")
            return {
                "summary": "Content analysis failed",
                "topics": [],
                "entities": [],
                "sentiment": "neutral",
                "keywords": [],
                "urgency": "low",
                "category": "general",
                "emotional_tone": "neutral",
                "action_items": [],
                "temporal_references": []
            } 