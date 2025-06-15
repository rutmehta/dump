package com.lifeos.android.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.lifeos.android.domain.models.ContentType
import com.lifeos.android.domain.models.MemoryMetadata
import com.lifeos.android.domain.models.Sentiment
import java.time.LocalDateTime

@Entity(tableName = "memories")
data class MemoryEntity(
    @PrimaryKey
    val id: String,
    val content: String,
    val contentType: ContentType,
    val timestamp: LocalDateTime,
    val userId: String,
    val metadata: MemoryMetadata,
    val entities: String, // JSON string of entities list
    val embedding: String?, // JSON string of float array
    val mediaUri: String?,
    val sentiment: Sentiment
)