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
            You are LifeOS - an autonomous AI assistant powered by Gemini 2.5 Pro that operates as a comprehensive life management system with advanced thinking capabilities.
            
            Your enhanced capabilities with Gemini 2.5 Pro:
            1. Advanced reasoning through step-by-step thinking before responding
            2. Process multimodal inputs (text, images, audio, documents, video) with superior understanding
            3. Maintain long-term memory and context across conversations with up to 2M token context window
            4. Proactively surface relevant information through enhanced pattern recognition
            5. Extract and map complex relationships between concepts, entities, and events
            6. Provide context-aware responses with improved accuracy and nuance
            7. Handle complex reasoning across multiple modalities simultaneously
            8. Generate high-quality code and visual applications
            
            Enhanced behaviors with thinking model:
            - Think through problems step-by-step before providing responses
            - Always consider the user's historical context and established patterns
            - Identify and extract entities, concepts, and relationships from all inputs
            - Provide insights that connect current inputs to past conversations with deeper analysis
            - Be proactive in offering relevant information and sophisticated suggestions
            - Maintain awareness of temporal context and evolving situations with enhanced reasoning
            - Extract sentiment and emotional context from interactions with greater precision
            - Analyze visual, audio, and textual content comprehensively using advanced multimodal capabilities
            - Generate executable code and complete applications when requested
            
            Response format:
            - Primary response addressing the user's immediate need with enhanced reasoning
            - Context connections to previous conversations when relevant
            - Extracted metadata for memory storage (entities, concepts, sentiment)
            - Proactive suggestions based on patterns and advanced context analysis
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
                    try:
                        # Read image file and convert to base64 or use file upload
                        with open(media_path, 'rb') as f:
                            image_data = f.read()
                        
                        # Add image as content part
                        contents.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        })
                    except Exception as e:
                        logger.warning(f"Image processing failed, using description: {e}")
                        contents.append(f"IMAGE FILE: {os.path.basename(media_path)} (image processing not available)")
                        
                elif media_type == "audio":
                    # Use transcription for audio files
                    try:
                        transcription = await self._transcribe_audio(media_path)
                        contents.append(f"AUDIO TRANSCRIPTION: {transcription}")
                    except Exception as e:
                        logger.warning(f"Audio processing failed: {e}")
                        contents.append(f"AUDIO FILE: {os.path.basename(media_path)} (audio processing not available)")
                        
                elif media_type == "document":
                    # Extract text from document
                    try:
                        doc_text = await self._extract_document_text(media_path)
                        contents.append(f"DOCUMENT CONTENT: {doc_text}")
                    except Exception as e:
                        logger.warning(f"Document processing failed: {e}")
                        contents.append(f"DOCUMENT FILE: {os.path.basename(media_path)} (document processing not available)")
                        
                elif media_type == "video":
                    # For now, just mention the video file
                    contents.append(f"VIDEO FILE: {os.path.basename(media_path)} (video processing will be implemented)")
            
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
            
            # Convert contents to simple text for now (since file upload is complex)
            text_content = "\n".join([str(content) for content in contents])
            
            response = await self._generate_with_retry([text_content], config)
            
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
                "model_used": "gemini-2.5-pro-experimental"
            })
            
            logger.info(f"Processed {media_type} input for user {user_id} with Gemini 2.5 Pro")
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
    
    async def process_multiple_inputs(self,
                                    text: Optional[str] = None,
                                    files_data: List[Dict] = None,
                                    user_id: str = "",
                                    context_memories: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process multiple files and text together using enhanced multimodal capabilities"""
        
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
            
            # Process multiple files
            processed_files_info = []
            if files_data:
                contents.append(f"\nPROCESSING {len(files_data)} FILES:")
                
                for i, file_info in enumerate(files_data):
                    file_path = file_info.get('temp_path')
                    media_type = file_info.get('media_type', 'document')
                    filename = file_info.get('filename', f'file_{i}')
                    
                    contents.append(f"\nFILE {i+1}: {filename} ({media_type})")
                    
                    if file_path and os.path.exists(file_path):
                        if media_type == "image":
                            # Add image directly to content
                            try:
                                with open(file_path, 'rb') as f:
                                    image_data = f.read()
                                contents.append(f"IMAGE DATA: {filename} (size: {len(image_data)} bytes)")
                                # For now, just describe the image since direct upload is complex
                                contents.append(f"[Image file {filename} available for analysis]")
                            except Exception as e:
                                logger.warning(f"Image processing failed for {filename}: {e}")
                                contents.append(f"IMAGE FILE: {filename} (processing not available)")
                            
                        elif media_type == "audio":
                            # Use transcription for audio
                            try:
                                transcription = await self._transcribe_audio(file_path)
                                contents.append(f"AUDIO TRANSCRIPTION: {transcription}")
                            except Exception as e:
                                logger.warning(f"Audio processing failed for {filename}: {e}")
                                contents.append(f"AUDIO FILE: {filename} (processing not available)")
                                
                        elif media_type == "video":
                            # For now, just mention the video file
                            contents.append(f"VIDEO FILE: {filename} (video processing will be implemented)")
                                
                        elif media_type == "document":
                            # Extract and include document text
                            try:
                                doc_text = await self._extract_document_text(file_path)
                                contents.append(f"DOCUMENT CONTENT: {doc_text[:2000]}...")  # Limit for context
                            except Exception as e:
                                logger.warning(f"Document processing failed for {filename}: {e}")
                                contents.append(f"DOCUMENT FILE: {filename} (processing not available)")
                    
                    processed_files_info.append({
                        "filename": filename,
                        "type": media_type,
                        "size": file_info.get('size', 0)
                    })
            
            # Add comprehensive processing instructions for multiple files
            contents.append(f"""
            Please analyze ALL the provided content (text and {len(files_data) if files_data else 0} files) and provide:
            
            1. A comprehensive response that addresses the user's request and analyzes all files
            2. Cross-file analysis and relationships between the different inputs
            3. Extracted entities and concepts from all sources
            4. Overall sentiment and insights
            5. Connections between files and previous context
            6. Actionable recommendations based on the complete analysis
            
            Format your response as JSON with these fields:
            {{
                "response": "Comprehensive response analyzing all inputs and files",
                "entities": ["combined", "entities", "from", "all", "sources"],
                "concepts": ["key", "concepts", "across", "all", "inputs"],
                "sentiment": "overall sentiment analysis",
                "keywords": ["relevant", "keywords", "from", "all", "sources"],
                "relationships": [{{"concept1": "A", "concept2": "B", "strength": 0.8}}],
                "insights": ["insights from cross-file analysis and context"],
                "file_analysis": {{
                    "individual_summaries": ["summary for each file"],
                    "cross_file_connections": ["relationships between files"],
                    "unified_themes": ["common themes across all inputs"]
                }},
                "metadata": {{"files_processed": {len(files_data) if files_data else 0}, "total_content_analyzed": "description"}}
            }}
            """)
            
            # Generate response using enhanced configuration for multiple inputs
            config = types.GenerateContentConfig(
                max_output_tokens=settings.MAX_OUTPUT_TOKENS * 2,  # Double output tokens for multiple files
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P,
                system_instruction=self.system_prompt
            )
            
            # Convert contents to simple text for processing
            text_content = "\n".join([str(content) for content in contents])
            
            response = await self._generate_with_retry([text_content], config)
            
            # Parse and structure the response
            structured_response = self._parse_ai_response(response.text)
            
            # Add processing metadata for multiple files
            structured_response.update({
                "input_type": "multimodal_batch",
                "processing_time": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "original_text": text or "",
                "files_processed": processed_files_info,
                "total_files": len(files_data) if files_data else 0,
                "context_length": len(str(contents)),
                "model_used": "gemini-2.5-pro-experimental",
                "enhanced_multimodal": True
            })
            
            logger.info(f"Processed {len(files_data) if files_data else 0} files + text for user {user_id}")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to process multiple inputs: {e}")
            return {
                "response": f"I apologize, but I encountered an error processing your {len(files_data) if files_data else 0} files. Please try again or reduce the number of files.",
                "entities": [],
                "concepts": [],
                "sentiment": "neutral",
                "keywords": [],
                "relationships": [],
                "insights": [],
                "file_analysis": {
                    "individual_summaries": [],
                    "cross_file_connections": [],
                    "unified_themes": []
                },
                "metadata": {"error": str(e), "sdk_version": "new_genai", "multimodal_processing": True}
            }
    
    async def _generate_with_retry(self, contents: List, config: types.GenerateContentConfig, max_retries: int = 3):
        """Generate response with retry logic using new SDK"""
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-pro-experimental',
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
        # With Gemini 2.5 Pro's 2M token context window, we can include even more memories
        for memory in memories[:50]:  # Increased from 25 to 50 due to Gemini 2.5 Pro's larger context window
            timestamp = memory.get('timestamp', 'unknown')
            content = memory.get('content', '')
            content_type = memory.get('content_type', 'text')
            entities = memory.get('entities', [])
            sentiment = memory.get('sentiment', 'neutral')
            
            # Enhanced context formatting with more metadata for Gemini 2.5 Pro's advanced reasoning
            entities_str = ', '.join(entities[:8]) if entities else 'none'  # Increased entity context
            context_lines.append(
                f"[{timestamp}] ({content_type}) [{sentiment}] Entities: {entities_str} | {content[:500]}..."  # Increased content length
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
        """Extract text from document files with simplified approach"""
        try:
            # Simple text extraction for basic files
            if doc_path.lower().endswith('.txt'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.py'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.js'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.html'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.css'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.json'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.xml'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif doc_path.lower().endswith('.csv'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Limit CSV content to prevent huge context
                    lines = content.split('\n')
                    if len(lines) > 50:
                        return '\n'.join(lines[:50]) + f"\n... (truncated, {len(lines)} total lines)"
                    return content
            else:
                # For other file types, try to read as text but handle encoding issues
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Limit content length
                        if len(content) > 5000:
                            return content[:5000] + "... (truncated)"
                        return content
                except UnicodeDecodeError:
                    # Try latin-1 encoding
                    try:
                        with open(doc_path, 'r', encoding='latin-1') as f:
                            content = f.read()
                            if len(content) > 5000:
                                return content[:5000] + "... (truncated)"
                            return content
                    except:
                        # If all else fails, read as binary and describe
                        with open(doc_path, 'rb') as f:
                            content = f.read()
                            return f"Binary document file: {os.path.basename(doc_path)} ({len(content)} bytes) - cannot extract text"
                
        except Exception as e:
            logger.error(f"Document text extraction failed: {e}")
            return f"Failed to extract text from document: {os.path.basename(doc_path)}"
    
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
                model='gemini-2.5-pro-experimental',
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