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
        val tvSummaryDescription: TextView = view.findViewById(R.id.tvSummaryDescription)
        val tvSummaryLabel: TextView = view.findViewById(R.id.tvSummaryLabel)
        val tvSummarySpeech: TextView = view.findViewById(R.id.tvSummarySpeech)
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
        holder.tvTime.text = item.published.take(16)

        // Summary from description
        if (!item.summary_description.isNullOrEmpty()) {
            holder.tvSummaryDescription.visibility = View.VISIBLE
            holder.tvSummaryDescription.text = item.summary_description
        } else {
            holder.tvSummaryDescription.visibility = View.GONE
        }

        // Summary from speech
        if (!item.summary_speech.isNullOrEmpty()) {
            holder.tvSummaryLabel.visibility = View.VISIBLE
            holder.tvSummarySpeech.visibility = View.VISIBLE
            holder.tvSummarySpeech.text = item.summary_speech
        } else {
            holder.tvSummaryLabel.visibility = View.GONE
            holder.tvSummarySpeech.visibility = View.GONE
        }

        holder.btnWatch.setOnClickListener {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(item.link))
            holder.itemView.context.startActivity(intent)
        }
    }

    override fun getItemCount() = items.size
}
