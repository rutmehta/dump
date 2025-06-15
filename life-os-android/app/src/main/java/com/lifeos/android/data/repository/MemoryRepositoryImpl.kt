package com.lifeos.android.data.repository

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.lifeos.android.data.local.dao.MemoryDao
import com.lifeos.android.data.local.entities.MemoryEntity
import com.lifeos.android.domain.models.Entity
import com.lifeos.android.domain.models.Memory
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.LocalDateTime
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MemoryRepositoryImpl @Inject constructor(
    private val memoryDao: MemoryDao
) : MemoryRepository {
    
    private val gson = Gson()
    
    override fun getAllMemories(): Flow<List<Memory>> {
        return memoryDao.getAllMemories().map { entities ->
            entities.map { it.toDomainModel() }
        }
    }
    
    override suspend fun getMemoryById(id: String): Memory? {
        return memoryDao.getMemoryById(id)?.toDomainModel()
    }
    
    override fun searchMemories(query: String): Flow<List<Memory>> {
        return memoryDao.searchMemories(query).map { entities ->
            entities.map { it.toDomainModel() }
        }
    }
    
    override fun getMemoriesBetweenDates(
        startDate: LocalDateTime,
        endDate: LocalDateTime
    ): Flow<List<Memory>> {
        return memoryDao.getMemoriesBetweenDates(startDate, endDate).map { entities ->
            entities.map { it.toDomainModel() }
        }
    }
    
    override suspend fun insertMemory(memory: Memory) {
        memoryDao.insertMemory(memory.toEntity())
    }
    
    override suspend fun updateMemory(memory: Memory) {
        memoryDao.updateMemory(memory.toEntity())
    }
    
    override suspend fun deleteMemory(memory: Memory) {
        memoryDao.deleteMemory(memory.toEntity())
    }
    
    override suspend fun deleteAllMemories() {
        memoryDao.deleteAllMemories()
    }
    
    private fun MemoryEntity.toDomainModel(): Memory {
        val entitiesList: List<Entity> = try {
            val type = object : TypeToken<List<Entity>>() {}.type
            gson.fromJson(entities, type)
        } catch (e: Exception) {
            emptyList()
        }
        
        val embeddingArray: FloatArray? = embedding?.let {
            try {
                gson.fromJson(it, FloatArray::class.java)
            } catch (e: Exception) {
                null
            }
        }
        
        return Memory(
            id = id,
            content = content,
            contentType = contentType,
            timestamp = timestamp,
            userId = userId,
            metadata = metadata,
            entities = entitiesList,
            embedding = embeddingArray,
            mediaUri = mediaUri,
            sentiment = sentiment
        )
    }
    
    private fun Memory.toEntity(): MemoryEntity {
        return MemoryEntity(
            id = id,
            content = content,
            contentType = contentType,
            timestamp = timestamp,
            userId = userId,
            metadata = metadata,
            entities = gson.toJson(entities),
            embedding = embedding?.let { gson.toJson(it) },
            mediaUri = mediaUri,
            sentiment = sentiment
        )
    }
}