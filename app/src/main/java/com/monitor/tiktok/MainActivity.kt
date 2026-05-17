package com.monitor.tiktok

import android.os.Bundle
import android.view.View
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.work.*
import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject
import java.net.URL
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    companion object {
        private const val FEED_URL =
            "https://raw.githubusercontent.com/clanpluse/TikTokMonitor/main/data/feed.json"
        private const val ACCOUNTS_URL =
            "https://raw.githubusercontent.com/clanpluse/TikTokMonitor/main/config/accounts.txt"
        private const val GITHUB_API =
            "https://api.github.com/repos/clanpluse/TikTokMonitor/contents/config/accounts.txt"
        private const val PREFS_NAME = "tiktok_prefs"
        private const val KEY_PAT = "pat_token"
    }

    private lateinit var recyclerFeed: RecyclerView
    private lateinit var tvEmpty: TextView
    private lateinit var tvStatus: TextView
    private lateinit var editAccount: EditText
    private lateinit var btnAdd: Button
    private lateinit var recyclerAccounts: RecyclerView
    private lateinit var accountsAdapter: AccountsAdapter

    private val accountsList = mutableListOf<String>()

    private fun getPatToken(): String {
        return getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
            .getString(KEY_PAT, "") ?: ""
    }

    private fun savePatToken(token: String) {
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
            .edit().putString(KEY_PAT, token).apply()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        recyclerFeed = findViewById(R.id.recyclerFeed)
        tvEmpty = findViewById(R.id.tvEmpty)
        tvStatus = findViewById(R.id.tvStatus)
        editAccount = findViewById(R.id.editAccount)
        btnAdd = findViewById(R.id.btnAdd)
        recyclerAccounts = findViewById(R.id.recyclerAccounts)

        recyclerFeed.layoutManager = LinearLayoutManager(this)

        accountsAdapter = AccountsAdapter(accountsList) { account ->
            removeAccount(account)
        }
        recyclerAccounts.layoutManager = LinearLayoutManager(this)
        recyclerAccounts.adapter = accountsAdapter

        btnAdd.setOnClickListener {
            val account = editAccount.text.toString().trim().removePrefix("@")
            if (account.isNotEmpty() && !accountsList.contains(account)) {
                addAccount(account)
                editAccount.text.clear()
            }
        }

        if (getPatToken().isEmpty()) {
            showTokenDialog()
        }

        scheduleMonitor()
        loadAccounts()
        loadFeed()
    }

    private fun showTokenDialog() {
        val input = EditText(this).apply {
            hint = "ghp_xxxxxxxxxxxxxxxxxx"
            inputType = android.text.InputType.TYPE_CLASS_TEXT
        }

        AlertDialog.Builder(this)
            .setTitle("GitHub Token")
            .setMessage("أدخل الـ Personal Access Token الخاص بك لإدارة الحسابات")
            .setView(input)
            .setCancelable(false)
            .setPositiveButton("حفظ") { _, _ ->
                val token = input.text.toString().trim()
                if (token.isNotEmpty()) {
                    savePatToken(token)
                    tvStatus.text = "تم حفظ الـ Token"
                }
            }
            .show()
    }

    private fun scheduleMonitor() {
        val request = PeriodicWorkRequestBuilder<MonitorWorker>(15, TimeUnit.MINUTES)
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            ).build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "tiktok_monitor",
            ExistingPeriodicWorkPolicy.KEEP,
            request
        )
    }

    private fun loadAccounts() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val text = URL(ACCOUNTS_URL).readText()
                val accounts = text.lines()
                    .map { it.trim() }
                    .filter { it.isNotEmpty() && !it.startsWith("#") }

                withContext(Dispatchers.Main) {
                    accountsList.clear()
                    accountsList.addAll(accounts)
                    accountsAdapter.notifyDataSetChanged()
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun addAccount(account: String) {
        accountsList.add(account)
        accountsAdapter.notifyItemInserted(accountsList.size - 1)
        updateAccountsOnGitHub()
    }

    private fun removeAccount(account: String) {
        val index = accountsList.indexOf(account)
        if (index != -1) {
            accountsList.removeAt(index)
            accountsAdapter.notifyItemRemoved(index)
            updateAccountsOnGitHub()
        }
    }

    private fun updateAccountsOnGitHub() {
        val token = getPatToken()
        if (token.isEmpty()) { showTokenDialog(); return }

        val content = accountsList.joinToString("\n")
        tvStatus.text = "جارٍ الحفظ..."

        CoroutineScope(Dispatchers.IO).launch {
            try {
                val getConn = URL(GITHUB_API).openConnection() as java.net.HttpURLConnection
                getConn.setRequestProperty("Authorization", "token $token")
                getConn.setRequestProperty("Accept", "application/vnd.github.v3+json")
                val getSha = JSONObject(getConn.inputStream.bufferedReader().readText()).getString("sha")
                getConn.disconnect()

                val encoded = android.util.Base64.encodeToString(
                    content.toByteArray(), android.util.Base64.NO_WRAP
                )

                val body = JSONObject().apply {
                    put("message", "Update accounts from app")
                    put("content", encoded)
                    put("sha", getSha)
                }

                val putConn = URL(GITHUB_API).openConnection() as java.net.HttpURLConnection
                putConn.requestMethod = "PUT"
                putConn.setRequestProperty("Authorization", "token $token")
                putConn.setRequestProperty("Accept", "application/vnd.github.v3+json")
                putConn.setRequestProperty("Content-Type", "application/json")
                putConn.doOutput = true
                putConn.outputStream.write(body.toString().toByteArray())
                putConn.responseCode
                putConn.disconnect()

                withContext(Dispatchers.Main) {
                    tvStatus.text = "تم الحفظ بنجاح"
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    tvStatus.text = "خطأ في الحفظ"
                }
            }
        }
    }

    private fun loadFeed() {
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
                        tvStatus.text = "لا توجد فيديوهات بعد"
                    } else {
                        tvEmpty.visibility = View.GONE
                        tvStatus.text = "${items.size} فيديو • يتحدث كل 15 دقيقة"
                        recyclerFeed.adapter = FeedAdapter(items)
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    tvStatus.text = "خطأ في التحميل"
                }
            }
        }
    }
}
