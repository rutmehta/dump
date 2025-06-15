package com.lifeos.android.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.lifeos.android.data.local.dao.MemoryDao
import com.lifeos.android.data.local.entities.MemoryEntity
import com.lifeos.android.data.local.converters.Converters

@Database(
    entities = [MemoryEntity::class],
    version = 1,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class LifeOSDatabase : RoomDatabase() {
    abstract fun memoryDao(): MemoryDao
    
    companion object {
        const val DATABASE_NAME = "lifeos_database"
    }
}