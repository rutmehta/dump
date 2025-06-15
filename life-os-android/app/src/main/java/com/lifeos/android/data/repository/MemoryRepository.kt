package com.lifeos.android.data.repository

import com.lifeos.android.domain.models.Memory
import kotlinx.coroutines.flow.Flow
import java.time.LocalDateTime

interface MemoryRepository {
    fun getAllMemories(): Flow<List<Memory>>
    suspend fun getMemoryById(id: String): Memory?
    fun searchMemories(query: String): Flow<List<Memory>>
    fun getMemoriesBetweenDates(startDate: LocalDateTime, endDate: LocalDateTime): Flow<List<Memory>>
    suspend fun insertMemory(memory: Memory)
    suspend fun updateMemory(memory: Memory)
    suspend fun deleteMemory(memory: Memory)
    suspend fun deleteAllMemories()
}