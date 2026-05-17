package com.monitor.tiktok

import android.content.Intent
import android.net.Uri
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class FeedAdapter(private val items: List<FeedItem>) :
    RecyclerView.Adapter<FeedAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvUsername: TextView = view.findViewById(R.id.tvUsername)
        val tvTitle: TextView = view.findViewById(R.id.tvTitle)
        val tvSummaryAi: TextView = view.findViewById(R.id.tvSummaryAi)
        val tvDescription: TextView = view.findViewById(R.id.tvDescription)
        val tvTime: TextView = view.findViewById(R.id.tvTime)
        val btnWatch: TextView = view.findViewById(R.id.btnWatch)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_feed, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = items[position]

        holder.tvUsername.text = "@${item.username}"
        holder.tvTitle.text = item.title

        if (!item.summary_ai.isNullOrEmpty()) {
            holder.tvSummaryAi.visibility = View.VISIBLE
            holder.tvSummaryAi.text = item.summary_ai
            holder.tvDescription.visibility = View.GONE
        } else {
            holder.tvSummaryAi.visibility = View.GONE
            holder.tvDescription.visibility = View.VISIBLE
            holder.tvDescription.text = item.description
        }

        holder.tvTime.text = item.published.take(16)

        holder.btnWatch.setOnClickListener {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(item.link))
            holder.itemView.context.startActivity(intent)
        }
    }

    override fun getItemCount() = items.size
}
