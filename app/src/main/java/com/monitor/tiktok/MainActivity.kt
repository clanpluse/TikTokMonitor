package com.monitor.tiktok

import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.work.*
import kotlinx.coroutines.*
import org.json.JSONArray
import java.net.URL
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    companion object {
        private const val FEED_URL =
            "https://raw.githubusercontent.com/clanpluse/TikTokMonitor/main/data/feed.json"
    }

    private lateinit var recyclerView: RecyclerView
    private lateinit var tvEmpty: TextView
    private lateinit var tvStatus: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        recyclerView = findViewById(R.id.recyclerFeed)
        tvEmpty = findViewById(R.id.tvEmpty)
        tvStatus = findViewById(R.id.tvStatus)

        recyclerView.layoutManager = LinearLayoutManager(this)

        scheduleMonitor()
        loadFeed()
    }

    private fun scheduleMonitor() {
        val request = PeriodicWorkRequestBuilder<MonitorWorker>(15, TimeUnit.MINUTES)
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "tiktok_monitor",
            ExistingPeriodicWorkPolicy.KEEP,
            request
        )
    }

    private fun loadFeed() {
        tvStatus.text = "جارٍ التحميل..."
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val json = URL(FEED_URL).readText()
                val array = JSONArray(json)
                val items = mutableListOf<FeedItem>()

                for (i in 0 until array.length()) {
                    val obj = array.getJSONObject(i)
                    items.add(
                        FeedItem(
                            id = obj.optString("id"),
                            username = obj.optString("username"),
                            title = obj.optString("title"),
                            description = obj.optString("description"),
                            link = obj.optString("link"),
                            published = obj.optString("published"),
                            timestamp = obj.optString("timestamp"),
                            summary_ai = obj.optString("summary_ai").ifEmpty { null }
                        )
                    )
                }

                withContext(Dispatchers.Main) {
                    if (items.isEmpty()) {
                        tvEmpty.visibility = View.VISIBLE
                        tvStatus.text = "لا توجد فيديوهات بعد — أضف حسابات في GitHub"
                    } else {
                        tvEmpty.visibility = View.GONE
                        tvStatus.text = "${items.size} فيديو • يتحدث كل 15 دقيقة"
                        recyclerView.adapter = FeedAdapter(items)
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    tvStatus.text = "خطأ في التحميل — تحقق من الاتصال"
                }
            }
        }
    }
}
