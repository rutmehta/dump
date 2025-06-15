package com.lifeos.android.domain.models

import java.time.LocalDateTime
import java.util.UUID

data class Memory(
    val id: String = UUID.randomUUID().toString(),
    val content: String,
    val contentType: ContentType,
    val timestamp: LocalDateTime = LocalDateTime.now(),
    val userId: String,
    val metadata: MemoryMetadata,
    val entities: List<Entity> = emptyList(),
    val embedding: FloatArray? = null,
    val mediaUri: String? = null,
    val sentiment: Sentiment = Sentiment.NEUTRAL
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as Memory

        if (id != other.id) return false
        if (content != other.content) return false
        if (contentType != other.contentType) return false
        if (timestamp != other.timestamp) return false
        if (userId != other.userId) return false
        if (metadata != other.metadata) return false
        if (entities != other.entities) return false
        if (embedding != null) {
            if (other.embedding == null) return false
            if (!embedding.contentEquals(other.embedding)) return false
        } else if (other.embedding != null) return false
        if (mediaUri != other.mediaUri) return false
        if (sentiment != other.sentiment) return false

        return true
    }

    override fun hashCode(): Int {
        var result = id.hashCode()
        result = 31 * result + content.hashCode()
        result = 31 * result + contentType.hashCode()
        result = 31 * result + timestamp.hashCode()
        result = 31 * result + userId.hashCode()
        result = 31 * result + metadata.hashCode()
        result = 31 * result + entities.hashCode()
        result = 31 * result + (embedding?.contentHashCode() ?: 0)
        result = 31 * result + (mediaUri?.hashCode() ?: 0)
        result = 31 * result + sentiment.hashCode()
        return result
    }
}

enum class ContentType {
    TEXT,
    IMAGE,
    AUDIO,
    VIDEO,
    DOCUMENT,
    MIXED
}

enum class Sentiment {
    POSITIVE,
    NEGATIVE,
    NEUTRAL
}

data class MemoryMetadata(
    val source: String = "manual",
    val location: Location? = null,
    val tags: List<String> = emptyList(),
    val priority: Priority = Priority.NORMAL,
    val isActionable: Boolean = false,
    val dueDate: LocalDateTime? = null,
    val relatedMemoryIds: List<String> = emptyList()
)

data class Location(
    val latitude: Double,
    val longitude: Double,
    val address: String? = null
)

enum class Priority {
    LOW,
    NORMAL,
    HIGH,
    URGENT
}

data class Entity(
    val id: String = UUID.randomUUID().toString(),
    val name: String,
    val type: EntityType,
    val confidence: Float = 1.0f
)

enum class EntityType {
    PERSON,
    PLACE,
    ORGANIZATION,
    DATE,
    TIME,
    MONEY,
    PHONE,
    EMAIL,
    URL,
    OTHER
}