package com.lifeos.android.domain.models

sealed class CaptureResult {
    data class Success(
        val memory: Memory,
        val processingTime: Long = 0L
    ) : CaptureResult()
    
    data class Error(
        val message: String,
        val exception: Exception? = null
    ) : CaptureResult()
    
    object Processing : CaptureResult()
}

data class MultimodalInput(
    val text: String? = null,
    val imageUri: String? = null,
    val audioUri: String? = null,
    val videoUri: String? = null,
    val documentUri: String? = null,
    val metadata: Map<String, Any> = emptyMap()
)

data class ProcessingResult(
    val content: String,
    val entities: List<Entity>,
    val sentiment: Sentiment,
    val keywords: List<String>,
    val summary: String? = null,
    val actionItems: List<ActionItem> = emptyList(),
    val suggestedFollowUps: List<String> = emptyList()
)

data class ActionItem(
    val id: String,
    val description: String,
    val type: ActionType,
    val dueDate: String? = null,
    val assignee: String? = null,
    val priority: Priority = Priority.NORMAL
)

enum class ActionType {
    TASK,
    REMINDER,
    FOLLOW_UP,
    MEETING,
    EMAIL,
    CALL,
    RESEARCH,
    OTHER
}