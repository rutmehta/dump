package com.lifeos.android.data.local.dao

import androidx.room.*
import com.lifeos.android.data.local.entities.MemoryEntity
import kotlinx.coroutines.flow.Flow
import java.time.LocalDateTime

@Dao
interface MemoryDao {
    @Query("SELECT * FROM memories ORDER BY timestamp DESC")
    fun getAllMemories(): Flow<List<MemoryEntity>>
    
    @Query("SELECT * FROM memories WHERE id = :memoryId")
    suspend fun getMemoryById(memoryId: String): MemoryEntity?
    
    @Query("SELECT * FROM memories WHERE timestamp BETWEEN :startDate AND :endDate ORDER BY timestamp DESC")
    fun getMemoriesBetweenDates(startDate: LocalDateTime, endDate: LocalDateTime): Flow<List<MemoryEntity>>
    
    @Query("SELECT * FROM memories WHERE content LIKE '%' || :query || '%' ORDER BY timestamp DESC")
    fun searchMemories(query: String): Flow<List<MemoryEntity>>
    
    @Query("SELECT * FROM memories WHERE userId = :userId ORDER BY timestamp DESC")
    fun getMemoriesByUser(userId: String): Flow<List<MemoryEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemory(memory: MemoryEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemories(memories: List<MemoryEntity>)
    
    @Update
    suspend fun updateMemory(memory: MemoryEntity)
    
    @Delete
    suspend fun deleteMemory(memory: MemoryEntity)
    
    @Query("DELETE FROM memories WHERE id = :memoryId")
    suspend fun deleteMemoryById(memoryId: String)
    
    @Query("DELETE FROM memories")
    suspend fun deleteAllMemories()
}