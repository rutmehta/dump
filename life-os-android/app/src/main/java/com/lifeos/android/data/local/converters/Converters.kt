package com.lifeos.android.data.local.converters

import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.lifeos.android.domain.models.*
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class Converters {
    private val gson = Gson()
    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME
    
    @TypeConverter
    fun fromLocalDateTime(dateTime: LocalDateTime?): String? {
        return dateTime?.format(dateFormatter)
    }
    
    @TypeConverter
    fun toLocalDateTime(dateTimeString: String?): LocalDateTime? {
        return dateTimeString?.let { LocalDateTime.parse(it, dateFormatter) }
    }
    
    @TypeConverter
    fun fromContentType(contentType: ContentType): String {
        return contentType.name
    }
    
    @TypeConverter
    fun toContentType(contentTypeString: String): ContentType {
        return ContentType.valueOf(contentTypeString)
    }
    
    @TypeConverter
    fun fromSentiment(sentiment: Sentiment): String {
        return sentiment.name
    }
    
    @TypeConverter
    fun toSentiment(sentimentString: String): Sentiment {
        return Sentiment.valueOf(sentimentString)
    }
    
    @TypeConverter
    fun fromMemoryMetadata(metadata: MemoryMetadata): String {
        return gson.toJson(metadata)
    }
    
    @TypeConverter
    fun toMemoryMetadata(metadataString: String): MemoryMetadata {
        return gson.fromJson(metadataString, MemoryMetadata::class.java)
    }
    
    @TypeConverter
    fun fromEntityList(entities: List<Entity>): String {
        return gson.toJson(entities)
    }
    
    @TypeConverter
    fun toEntityList(entitiesString: String): List<Entity> {
        val type = object : TypeToken<List<Entity>>() {}.type
        return gson.fromJson(entitiesString, type)
    }
    
    @TypeConverter
    fun fromFloatArray(floatArray: FloatArray?): String? {
        return floatArray?.let { gson.toJson(it) }
    }
    
    @TypeConverter
    fun toFloatArray(floatArrayString: String?): FloatArray? {
        return floatArrayString?.let { gson.fromJson(it, FloatArray::class.java) }
    }
}