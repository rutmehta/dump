package com.lifeos.android.domain.usecases

import android.net.Uri
import com.lifeos.android.domain.models.CaptureResult
import kotlinx.coroutines.flow.Flow

interface CaptureUseCase {
    suspend fun captureText(text: String): Flow<CaptureResult>
    suspend fun captureAudio(audioUri: Uri): Flow<CaptureResult>
    suspend fun captureImage(imageUri: Uri): Flow<CaptureResult>
    suspend fun captureVideo(videoUri: Uri): Flow<CaptureResult>
    suspend fun captureDocument(docUri: Uri): Flow<CaptureResult>
    suspend fun captureMultimodal(
        text: String? = null,
        mediaUris: List<Uri> = emptyList()
    ): Flow<CaptureResult>
}