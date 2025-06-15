package com.lifeos.android.services

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.content
import com.google.ai.client.generativeai.type.generationConfig
import com.lifeos.android.domain.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class GeminiAIService(
    private val context: Context,
    private val apiKey: String
) {
    
    private val model by lazy {
        GenerativeModel(
            modelName = "gemini-1.5-pro",
            apiKey = apiKey,
            generationConfig = generationConfig {
                temperature = 0.7f
                maxOutputTokens = 8192
            }
        )
    }
    
    suspend fun processMultimodal(
        inputs: List<MultimodalInput>
    ): ProcessingResult = withContext(Dispatchers.IO) {
        try {
            val prompt = buildPrompt(inputs)
            val contentBuilder = content {
                text(prompt)
                
                // Add images if present
                inputs.forEach { input ->
                    input.imageUri?.let { uri ->
                        val bitmap = loadBitmapFromUri(Uri.parse(uri))
                        bitmap?.let { image(it) }
                    }
                }
            }
            
            val response = model.generateContent(contentBuilder)
            parseResponse(response.text ?: "")
        } catch (e: Exception) {
            ProcessingResult(
                content = inputs.firstOrNull()?.text ?: "",
                entities = emptyList(),
                sentiment = Sentiment.NEUTRAL,
                keywords = emptyList(),
                summary = null,
                actionItems = emptyList(),
                suggestedFollowUps = emptyList()
            )
        }
    }
    
    private fun buildPrompt(inputs: List<MultimodalInput>): String {
        return """
            You are an AI assistant helping to process and understand user inputs.
            
            Analyze the following content and provide:
            1. Extracted entities (people, places, organizations, dates, etc.)
            2. Overall sentiment (positive, negative, neutral)
            3. Key keywords and concepts
            4. A brief summary if the content is long
            5. Any actionable items mentioned
            6. Suggested follow-up actions
            
            Content to analyze:
            ${inputs.joinToString("\n") { it.text ?: "[Non-text content]" }}
            
            Respond in the following JSON format:
            {
                "content": "processed content",
                "entities": [{"name": "entity", "type": "PERSON/PLACE/etc", "confidence": 0.95}],
                "sentiment": "POSITIVE/NEGATIVE/NEUTRAL",
                "keywords": ["keyword1", "keyword2"],
                "summary": "brief summary or null",
                "actionItems": [{"description": "task", "type": "TASK/REMINDER/etc", "priority": "HIGH/NORMAL/LOW"}],
                "suggestedFollowUps": ["follow up 1", "follow up 2"]
            }
        """.trimIndent()
    }
    
    private fun parseResponse(response: String): ProcessingResult {
        // In a real implementation, you would parse the JSON response
        // For now, returning a mock result
        return ProcessingResult(
            content = response,
            entities = listOf(
                Entity(name = "Sample Entity", type = EntityType.OTHER)
            ),
            sentiment = Sentiment.NEUTRAL,
            keywords = listOf("sample", "keyword"),
            summary = "This is a sample summary",
            actionItems = emptyList(),
            suggestedFollowUps = listOf("Review this later", "Share with team")
        )
    }
    
    private suspend fun loadBitmapFromUri(uri: Uri): Bitmap? {
        return withContext(Dispatchers.IO) {
            try {
                context.contentResolver.openInputStream(uri)?.use { inputStream ->
                    BitmapFactory.decodeStream(inputStream)
                }
            } catch (e: Exception) {
                null
            }
        }
    }
    
    suspend fun generateEmbedding(text: String): FloatArray {
        // This would use a text embedding model
        // For now, return a mock embedding
        return FloatArray(768) { it.toFloat() / 768f }
    }
}