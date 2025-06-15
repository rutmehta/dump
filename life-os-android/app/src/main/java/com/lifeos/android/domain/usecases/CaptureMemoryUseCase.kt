package com.lifeos.android.domain.usecases

import com.lifeos.android.data.repository.MemoryRepository
import com.lifeos.android.domain.models.*
import com.lifeos.android.services.GeminiAIService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.util.UUID
import javax.inject.Inject

class CaptureMemoryUseCase @Inject constructor(
    private val memoryRepository: MemoryRepository,
    private val geminiAIService: GeminiAIService
) {
    
    suspend operator fun invoke(
        input: MultimodalInput,
        userId: String = "default_user" // In production, get from auth service
    ): Flow<CaptureResult> = flow {
        emit(CaptureResult.Processing)
        
        try {
            // Process the input with AI
            val processingResult = geminiAIService.processMultimodal(listOf(input))
            
            // Generate embedding for the content
            val embedding = input.text?.let { 
                geminiAIService.generateEmbedding(it)
            }
            
            // Create memory object
            val memory = Memory(
                id = UUID.randomUUID().toString(),
                content = processingResult.content,
                contentType = determineContentType(input),
                userId = userId,
                metadata = MemoryMetadata(
                    source = "manual_capture",
                    tags = processingResult.keywords,
                    isActionable = processingResult.actionItems.isNotEmpty(),
                    dueDate = processingResult.actionItems.firstOrNull()?.dueDate?.let {
                        // Parse due date - simplified for now
                        null
                    }
                ),
                entities = processingResult.entities,
                embedding = embedding,
                mediaUri = input.imageUri ?: input.audioUri ?: input.videoUri ?: input.documentUri,
                sentiment = processingResult.sentiment
            )
            
            // Save to repository
            memoryRepository.insertMemory(memory)
            
            emit(CaptureResult.Success(memory))
        } catch (e: Exception) {
            emit(CaptureResult.Error(
                message = "Failed to capture memory: ${e.message}",
                exception = e
            ))
        }
    }
    
    private fun determineContentType(input: MultimodalInput): ContentType {
        return when {
            input.imageUri != null -> ContentType.IMAGE
            input.audioUri != null -> ContentType.AUDIO
            input.videoUri != null -> ContentType.VIDEO
            input.documentUri != null -> ContentType.DOCUMENT
            input.text != null -> ContentType.TEXT
            else -> ContentType.MIXED
        }
    }
}