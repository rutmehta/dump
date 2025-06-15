package com.lifeos.android.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeos.android.data.repository.MemoryRepository
import com.lifeos.android.domain.models.Memory
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class SearchMode {
    SEMANTIC,
    KEYWORD,
    HYBRID
}

data class SearchUiState(
    val searchResults: List<Memory> = emptyList(),
    val isLoading: Boolean = false,
    val searchMode: SearchMode = SearchMode.HYBRID,
    val error: String? = null
)

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val memoryRepository: MemoryRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()
    
    private var searchJob: Job? = null
    
    fun search(query: String) {
        searchJob?.cancel()
        
        if (query.isBlank()) {
            clearSearch()
            return
        }
        
        searchJob = viewModelScope.launch {
            // Debounce search
            delay(300)
            
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            try {
                when (_uiState.value.searchMode) {
                    SearchMode.KEYWORD -> {
                        memoryRepository.searchMemories(query).collect { memories ->
                            _uiState.update { 
                                it.copy(
                                    searchResults = memories,
                                    isLoading = false
                                )
                            }
                        }
                    }
                    SearchMode.SEMANTIC -> {
                        // TODO: Implement semantic search using embeddings
                        // For now, fall back to keyword search
                        memoryRepository.searchMemories(query).collect { memories ->
                            _uiState.update { 
                                it.copy(
                                    searchResults = memories,
                                    isLoading = false
                                )
                            }
                        }
                    }
                    SearchMode.HYBRID -> {
                        // TODO: Implement hybrid search combining semantic and keyword
                        // For now, use keyword search
                        memoryRepository.searchMemories(query).collect { memories ->
                            _uiState.update { 
                                it.copy(
                                    searchResults = memories,
                                    isLoading = false
                                )
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        error = "Search failed: ${e.message}"
                    )
                }
            }
        }
    }
    
    fun setSearchMode(mode: SearchMode) {
        _uiState.update { it.copy(searchMode = mode) }
        // Re-run search with new mode if there's an active query
        val currentQuery = _uiState.value.searchResults.firstOrNull()?.content
        if (!currentQuery.isNullOrBlank()) {
            search(currentQuery)
        }
    }
    
    fun clearSearch() {
        searchJob?.cancel()
        _uiState.update { 
            it.copy(
                searchResults = emptyList(),
                isLoading = false,
                error = null
            )
        }
    }
}