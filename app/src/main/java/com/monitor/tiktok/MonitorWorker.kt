package com.monitor.tiktok

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.Worker
import androidx.work.WorkerParameters
import org.json.JSONArray
import java.net.URL

class MonitorWorker(ctx: Context, params: WorkerParameters) : Worker(ctx, params) {

    companion object {
        private const val FEED_URL =
            "https://raw.githubusercontent.com/clanpluse/TikTokMonitor/main/data/feed.json"
        private const val CHANNEL_ID = "tiktok_alerts"
        private const val PREFS_NAME = "tiktok_monitor"
        private const val KEY_LAST_ID = "last_seen_id"
    }

    override fun doWork(): Result {
        return try {
            val json = URL(FEED_URL).readText()
            val array = JSONArray(json)
            if (array.length() == 0) return Result.success()

            val prefs = applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val lastSeenId = prefs.getString(KEY_LAST_ID, null)

            val newItems = mutableListOf<Triple<String, String, String?>>()

            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                val id = obj.optString("id")
                if (id == lastSeenId) break
                newItems.add(
                    Triple(
                        obj.optString("username"),
                        obj.optString("title"),
                        obj.optString("summary_ai").ifEmpty { null }
                    )
                )
            }

            if (newItems.isNotEmpty()) {
                val firstId = array.getJSONObject(0).optString("id")
                prefs.edit().putString(KEY_LAST_ID, firstId).apply()
                newItems.forEach { (username, title, summary) ->
                    sendNotification(username, title, summary)
                }
            }

            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun sendNotification(username: String, title: String, summary: String?) {
        createChannel()
        val intent = Intent(applicationContext, MainActivity::class.java)
        val pending = PendingIntent.getActivity(
            applicationContext, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val bodyText = summary ?: title
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("فيديو جديد من @$username")
            .setContentText(title)
            .setStyle(NotificationCompat.BigTextStyle().bigText(bodyText))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pending)
            .build()

        val manager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE)
                as NotificationManager
        manager.notify(System.currentTimeMillis().toInt(), notification)
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID, "تنبيهات تيك توك",
                NotificationManager.IMPORTANCE_HIGH
            )
            val manager = applicationContext.getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
}
