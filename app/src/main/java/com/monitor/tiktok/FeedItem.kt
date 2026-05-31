package com.monitor.tiktok

data class FeedItem(
    val id: String,
    val username: String,
    val title: String,
    val description: String,
    val link: String,
    val published: String,
    val timestamp: String,
    val summary_description: String?,
    val summary_speech: String?
)
