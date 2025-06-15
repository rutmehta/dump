package com.lifeos.android.ui.screens

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeos.android.domain.models.CaptureResult
import com.lifeos.android.domain.models.Memory
import com.lifeos.android.domain.models.MultimodalInput
import com.lifeos.android.domain.usecases.CaptureMemoryUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CaptureUiState(
    val isProcessing: Boolean = false,
    val recentMemories: List<Memory> = emptyList(),
    val error: String? = null,
    val successMessage: String? = null
)

@HiltViewModel
class CaptureViewModel @Inject constructor(
    private val captureMemoryUseCase: CaptureMemoryUseCase
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(CaptureUiState())
    val uiState: StateFlow<CaptureUiState> = _uiState.asStateFlow()
    
    fun captureText(text: String) {
        viewModelScope.launch {
            val input = MultimodalInput(text = text)
            captureMemoryUseCase(input).collect { result ->
                handleCaptureResult(result)
            }
        }
    }
    
    fun captureImage(uri: Uri) {
        viewModelScope.launch {
            val input = MultimodalInput(imageUri = uri.toString())
            captureMemoryUseCase(input).collect { result ->
                handleCaptureResult(result)
            }
        }
    }
    
    fun captureAudio(uri: Uri) {
        viewModelScope.launch {
            val input = MultimodalInput(audioUri = uri.toString())
            captureMemoryUseCase(input).collect { result ->
                handleCaptureResult(result)
            }
        }
    }
    
    fun captureVideo(uri: Uri) {
        viewModelScope.launch {
            val input = MultimodalInput(videoUri = uri.toString())
            captureMemoryUseCase(input).collect { result ->
                handleCaptureResult(result)
            }
        }
    }
    
    fun captureDocument(uri: Uri) {
        viewModelScope.launch {
            val input = MultimodalInput(documentUri = uri.toString())
            captureMemoryUseCase(input).collect { result ->
                handleCaptureResult(result)
            }
        }
    }
    
    fun captureMultimodal(text: String?, mediaUris: List<Uri>) {
        viewModelScope.launch {
            val input = MultimodalInput(
                text = text,
                imageUri = mediaUris.firstOrNull { it.toString().contains("image") }?.toString(),
                audioUri = mediaUris.firstOrNull { it.toString().contains("audio") }?.toString(),
                videoUri = mediaUris.firstOrNull { it.toString().contains("video") }?.toString(),
                documentUri = mediaUris.firstOrNull { it.toString().contains("document") || it.toString().contains("pdf") }?.toString()
            )
            captureMemoryUseCase(input).collect { result ->
                handleCaptureResult(result)
            }
        }
    }
    
    private fun handleCaptureResult(result: CaptureResult) {
        when (result) {
            is CaptureResult.Processing -> {
                _uiState.update { it.copy(isProcessing = true, error = null) }
            }
            is CaptureResult.Success -> {
                _uiState.update { currentState ->
                    currentState.copy(
                        isProcessing = false,
                        recentMemories = listOf(result.memory) + currentState.recentMemories.take(9),
                        successMessage = "Captured successfully!",
                        error = null
                    )
                }
                // Clear success message after delay
                viewModelScope.launch {
                    kotlinx.coroutines.delay(3000)
                    _uiState.update { it.copy(successMessage = null) }
                }
            }
            is CaptureResult.Error -> {
                _uiState.update { 
                    it.copy(
                        isProcessing = false,
                        error = result.message
                    )
                }
            }
        }
    }
    
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}