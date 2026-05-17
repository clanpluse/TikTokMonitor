package com.monitor.tiktok

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class AccountsAdapter(
    private val accounts: MutableList<String>,
    private val onDelete: (String) -> Unit
) : RecyclerView.Adapter<AccountsAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvAccount: TextView = view.findViewById(R.id.tvAccount)
        val btnDelete: ImageButton = view.findViewById(R.id.btnDeleteAccount)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_account, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val account = accounts[position]
        holder.tvAccount.text = "@$account"
        holder.btnDelete.setOnClickListener { onDelete(account) }
    }

    override fun getItemCount() = accounts.size
}
