package com.lifeos.android.di

import android.content.Context
import androidx.room.Room
import com.lifeos.android.data.local.LifeOSDatabase
import com.lifeos.android.data.local.dao.MemoryDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideLifeOSDatabase(
        @ApplicationContext context: Context
    ): LifeOSDatabase {
        return Room.databaseBuilder(
            context,
            LifeOSDatabase::class.java,
            LifeOSDatabase.DATABASE_NAME
        )
            .fallbackToDestructiveMigration()
            .build()
    }
    
    @Provides
    @Singleton
    fun provideMemoryDao(database: LifeOSDatabase): MemoryDao {
        return database.memoryDao()
    }
}