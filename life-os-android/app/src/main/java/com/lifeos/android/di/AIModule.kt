package com.lifeos.android.di

import android.content.Context
import com.lifeos.android.BuildConfig
import com.lifeos.android.services.GeminiAIService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Named
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AIModule {
    
    @Provides
    @Named("gemini_api_key")
    fun provideGeminiApiKey(): String {
        // In production, this should come from secure storage or build config
        return BuildConfig.GEMINI_API_KEY
    }
    
    @Provides
    @Singleton
    fun provideGeminiAIService(
        @ApplicationContext context: Context,
        @Named("gemini_api_key") apiKey: String
    ): GeminiAIService {
        return GeminiAIService(context, apiKey)
    }
}