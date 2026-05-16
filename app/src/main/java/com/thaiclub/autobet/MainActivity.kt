package com.thaiclub.autobet

import android.app.AlertDialog
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var tabJwt: Button
    private lateinit var tabCred: Button
    private lateinit var panelJwt: LinearLayout
    private lateinit var panelCred: LinearLayout
    private lateinit var etJwt: EditText
    private lateinit var etUsername: EditText
    private lateinit var etPassword: EditText
    private lateinit var spGame: Spinner
    private lateinit var spStrategy: Spinner
    private lateinit var etBetAmount: EditText
    private lateinit var etRounds: EditText
    private lateinit var btnConnect: Button
    private lateinit var btnStart: Button
    private lateinit var btnPause: Button
    private lateinit var btnRefresh: Button
    private lateinit var btnHistory: Button
    private lateinit var btnSettings: Button
    private lateinit var tvStatus: TextView
    private lateinit var tvBalance: TextView
    private lateinit var tvClock: TextView
    private lateinit var tvLog: TextView
    private lateinit var tvRounds: TextView
    private lateinit var tvWins: TextView
    private lateinit var tvLosses: TextView
    private lateinit var tvPL: TextView
    private lateinit var logScrollView: ScrollView
    private lateinit var progressBar: ProgressBar
    private lateinit var statsRow: LinearLayout

    private val client = OkHttpClient()
    private val BASE   = "https://api.thaiclub1.us.cc"
    private var jwtToken  = ""
    private var balance   = 0.0
    private var initBal   = 0.0
    private var oldBal    = 0.0
    private val history   = mutableListOf<BetRecord>()
    private var running   = false
    private var paused    = false
    private var rounds    = 0
    private var wins      = 0
    private var losses    = 0
    private var sessionPL = 0.0
    private var curBet    = 10.0
    private var baseBet   = 10.0
    private var lastResult = ""
    private var betJob: Job? = null
    private val handler = Handler(Looper.getMainLooper())

    private var trigSec1   = 26;  private var trigSec2   = 57
    private var fetchSec1  = 20;  private var fetchSec2  = 50
    private var balSec1    = 10;  private var balSec2    = 40
    private var settleDly  = 10
    private var stopProfit = 0.0; private var stopLoss   = 0.0
    private var maxRounds  = 10

    private val games = listOf(
        "30S" to "Win Go 30 Sec",
        "1MIN" to "Win Go 1 Min",
        "3MIN" to "Win Go 3 Min",
        "5MIN" to "Win Go 5 Min"
    )
    private val strategies = listOf(
        "Mirror","Opposite","Random Opposite","Martingale","Anti-Martingale"
    )

    data class BetRecord(
        val round: Int, val issue: String, val betType: String,
        val amount: Double, val win: Boolean, val pl: Double, val balance: Double
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        bindViews(); setupSpinners(); setupListeners(); startClock()
    }

    private fun bindViews() {
        tabJwt       = findViewById(R.id.tabJwt)
        tabCred      = findViewById(R.id.tabCred)
        panelJwt     = findViewById(R.id.panelJwt)
        panelCred    = findViewById(R.id.panelCred)
        etJwt        = findViewById(R.id.etJwt)
        etUsername   = findViewById(R.id.etUsername)
        etPassword   = findViewById(R.id.etPassword)
        spGame       = findViewById(R.id.spGame)
        spStrategy   = findViewById(R.id.spStrategy)
        etBetAmount  = findViewById(R.id.etBetAmount)
        etRounds     = findViewById(R.id.etRounds)
        btnConnect   = findViewById(R.id.btnConnect)
        btnStart     = findViewById(R.id.btnStart)
        btnPause     = findViewById(R.id.btnPause)
        btnRefresh   = findViewById(R.id.btnRefresh)
        btnHistory   = findViewById(R.id.btnHistory)
        btnSettings  = findViewById(R.id.btnSettings)
        tvStatus     = findViewById(R.id.tvStatus)
        tvBalance    = findViewById(R.id.tvBalance)
        tvClock      = findViewById(R.id.tvClock)
        tvLog        = findViewById(R.id.tvLog)
        tvRounds     = findViewById(R.id.tvRounds)
        tvWins       = findViewById(R.id.tvWins)
        tvLosses     = findViewById(R.id.tvLosses)
        tvPL         = findViewById(R.id.tvPL)
        logScrollView= findViewById(R.id.logScrollView)
        progressBar  = findViewById(R.id.progressBar)
        statsRow     = findViewById(R.id.statsRow)
    }

    private fun setupSpinners() {
        spGame.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item, games.map { it.second })
        spStrategy.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item, strategies)
    }

    private fun setupListeners() {
        tabJwt.setOnClickListener {
            panelJwt.visibility = View.VISIBLE; panelCred.visibility = View.GONE
            tabJwt.backgroundTintList  = getColorStateList(R.color.accent)
            tabCred.backgroundTintList = getColorStateList(R.color.surface2)
        }
        tabCred.setOnClickListener {
            panelJwt.visibility = View.GONE; panelCred.visibility = View.VISIBLE
            tabCred.backgroundTintList = getColorStateList(R.color.accent)
            tabJwt.backgroundTintList  = getColorStateList(R.color.surface2)
        }
        btnConnect.setOnClickListener  { doConnect() }
        btnStart.setOnClickListener    { if (!running) startBot() }
        btnPause.setOnClickListener    { togglePause() }
        btnRefresh.setOnClickListener  { CoroutineScope(Dispatchers.IO).launch { fetchBalance() } }
        btnHistory.setOnClickListener  { showHistory() }
        btnSettings.setOnClickListener { showSettings() }
    }

    private fun startClock() {
        handler.post(object : Runnable {
            override fun run() {
                val cal    = Calendar.getInstance()
                val sec    = cal.get(Calendar.SECOND)
                val is30S  = games[spGame.selectedItemPosition].first == "30S"
                val cycLen = if (is30S) 30 else 60
                val cycSec = if (is30S) sec % 30 else sec
                progressBar.progress = (cycSec * 100) / cycLen
                val t1 = if (is30S) trigSec1 % 30 else trigSec1
                val t2 = if (is30S) trigSec2 % 30 else -1
                val tStr = if (t2 >= 0) "Bet@${t1}s+${t2}s" else "Bet@${t1}s"
                tvClock.text = "%02d:%02d:%02d  %s  cycle=%ds/%ds  %s".format(
                    cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE), sec,
                    games[spGame.selectedItemPosition].second, cycSec, cycLen, tStr)
                handler.postDelayed(this, 500)
            }
        })
    }

    private fun doConnect() {
        if (panelJwt.visibility == View.VISIBLE) {
            val t = etJwt.text.toString().trim()
            if (t.isEmpty()) { toast("Paste JWT token"); return }
            jwtToken = if (t.startsWith("Bearer ")) t else "Bearer $t"
            log("AUTH", "JWT token set ✓")
            CoroutineScope(Dispatchers.IO).launch { fetchBalance() }
        } else {
            val phone = etUsername.text.toString().trim()
            val pass  = etPassword.text.toString().trim()
            if (phone.isEmpty() || pass.isEmpty()) { toast("Enter phone and password"); return }
            CoroutineScope(Dispatchers.IO).launch { doLogin(phone, pass) }
        }
    }

    private suspend fun doLogin(phone: String, pass: String) {
        runOnUiThread { tvStatus.text = "🔄 Logging in..." }
        try {
            val ts  = (System.currentTimeMillis()/1000).toString()
            val sig = md5("${phone}&${pass}&${ts}&R2Ks_5Fq")
            val body = JSONObject().apply {
                put("phone", phone); put("password", pass)
                put("timestamp", ts); put("signature", sig)
                put("packId", ""); put("deviceId", "android_device")
                put("phonetype", "android"); put("logintype", "1"); put("language", 0)
            }.toString().toRequestBody("application/json".toMediaType())
            val resp = client.newCall(Request.Builder().url("$BASE/api/webapi/Login")
                .post(body).addHeader("Content-Type","application/json").build()).await()
            val json = JSONObject(resp.body?.string() ?: "{}")
            if (json.optInt("code") == 0) {
                jwtToken = "Bearer ${json.optJSONObject("data")?.optString("token","") ?: ""}"
                log("AUTH", "✅ Logged in as $phone")
                fetchBalance()
            } else {
                runOnUiThread { tvStatus.text = "❌ Login: ${json.optString("msg")}" }
            }
        } catch (e: Exception) { runOnUiThread { tvStatus.text = "❌ ${e.message}" } }
    }

    private suspend fun fetchBalance() {
        if (jwtToken.isEmpty()) return
        try {
            val resp = client.newCall(Request.Builder()
                .url("$BASE/api/webapi/GetAccountInfo").get()
                .addHeader("Authorization", jwtToken).build()).await()
            val json = JSONObject(resp.body?.string() ?: "{}")
            val b = json.optJSONObject("data")?.optDouble("balance", balance) ?: balance
            balance = b
            if (initBal == 0.0) initBal = b
            runOnUiThread {
                tvBalance.text = "💰 ₹%.2f".format(b)
                tvStatus.text  = "✅ Connected — ₹%.2f".format(b)
                statsRow.visibility = View.VISIBLE
            }
        } catch (e: Exception) { runOnUiThread { tvStatus.text = "❌ ${e.message}" } }
    }

    private fun startBot() {
        if (jwtToken.isEmpty()) { toast("Connect first"); return }
        running = true; paused = false
        baseBet = etBetAmount.text.toString().toDoubleOrNull() ?: 10.0
        curBet  = baseBet
        maxRounds = etRounds.text.toString().toIntOrNull() ?: 10
        rounds = 0; wins = 0; losses = 0; sessionPL = 0.0; history.clear(); initBal = 0.0
        btnStart.text = "⏹  RUNNING"; btnStart.isEnabled = false
        val gameKey = games[spGame.selectedItemPosition].first
        val is30S   = gameKey == "30S"
        log("SYS","🚀 Started | Bet=₹$baseBet | Rounds=$maxRounds | ${strategies[spStrategy.selectedItemPosition]}")
        betJob = CoroutineScope(Dispatchers.IO).launch { botLoop(gameKey, is30S) }
    }

    private fun stopBot(reason: String) {
        running = false; betJob?.cancel()
        runOnUiThread {
            btnStart.text = "▶  START"; btnStart.isEnabled = true
            btnPause.text = "⏸  PAUSE"
            log("SYS","🛑 $reason | P/L: ₹%.2f | W$wins/L$losses".format(sessionPL))
            tvStatus.text = "Stopped: $reason"
        }
    }

    private fun togglePause() {
        if (!running) return
        paused = !paused
        runOnUiThread { btnPause.text = if (paused) "▶  RESUME" else "⏸  PAUSE" }
        log("SYS", if (paused) "⏸ Paused" else "▶ Resumed")
    }

    private suspend fun botLoop(gameKey: String, is30S: Boolean) {
        var cachedIssue = ""; var lastFetchKey = ""; var lastBetKey = ""
        while (running) {
            if (paused) { delay(500); continue }
            if (rounds >= maxRounds) { stopBot("Max rounds"); break }
            if (stopProfit > 0 && sessionPL >= stopProfit) { stopBot("Stop Profit ₹$stopProfit"); break }
            if (stopLoss   > 0 && sessionPL <= -stopLoss)  { stopBot("Stop Loss ₹$stopLoss");   break }

            val cal    = Calendar.getInstance()
            val sec    = cal.get(Calendar.SECOND)
            val cycSec = if (is30S) sec % 30 else sec
            val cycKey = if (is30S) {
                "%02d%02d-%s".format(cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE),
                    if (sec < 30) "A" else "B")
            } else {
                "%02d%02d".format(cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE))
            }

            val f1 = fetchSec1 % (if (is30S) 30 else 60)
            val f2 = if (is30S) fetchSec2 % 30 else -1
            val t1 = trigSec1  % (if (is30S) 30 else 60)
            val t2 = if (is30S) trigSec2 % 30 else -1
            val b1 = balSec1   % (if (is30S) 30 else 60)
            val b2 = if (is30S) balSec2 % 30 else -1

            if ((cycSec == f1 || (f2 >= 0 && cycSec == f2)) && lastFetchKey != cycKey) {
                lastFetchKey = cycKey
                cachedIssue = fetchIssue(gameKey)
                log("FETCH","Issue=$cachedIssue")
            }
            if ((cycSec == b1 || (b2 >= 0 && cycSec == b2)) && lastBetKey != cycKey) {
                oldBal = balance; fetchBalance()
            }
            if ((cycSec == t1 || (t2 >= 0 && cycSec == t2)) && lastBetKey != cycKey) {
                lastBetKey = cycKey
                if (cachedIssue.isEmpty()) cachedIssue = fetchIssue(gameKey)
                val betType = decideBet()
                val ok = placeBet(gameKey, cachedIssue, betType, curBet)
                if (ok) {
                    rounds++
                    runOnUiThread { tvRounds.text = rounds.toString() }
                    log("BET","#$rounds Issue=$cachedIssue Type=$betType Amt=₹$curBet")
                    cachedIssue = ""
                    delay(settleDly * 1000L)
                    settle(betType)
                }
            }
            delay(300)
        }
    }

    private fun decideBet(): String {
        return when (strategies[spStrategy.selectedItemPosition]) {
            "Mirror"          -> if (lastResult.isEmpty()) "B" else lastResult
            "Opposite"        -> if (lastResult == "B") "S" else "B"
            "Random Opposite" -> if (lastResult.isEmpty()) listOf("B","S").random()
                                  else if (listOf(true,false).random()) (if(lastResult=="B")"S" else "B")
                                  else lastResult
            "Martingale"      -> if (lastResult == "L") "B" else "S"
            "Anti-Martingale" -> if (lastResult == "W") "B" else "S"
            else -> listOf("B","S").random()
        }
    }

    private suspend fun fetchIssue(gameKey: String): String {
        return try {
            val tid = typeId(gameKey)
            val r = client.newCall(Request.Builder()
                .url("$BASE/api/webapi/GetGameIssue?typeId=$tid").get()
                .addHeader("Authorization", jwtToken).build()).await()
            JSONObject(r.body?.string() ?: "{}").optJSONObject("data")
                ?.optString("issueNumber") ?: ""
        } catch (e: Exception) { "" }
    }

    private suspend fun placeBet(gameKey: String, issue: String, betType: String, amount: Double): Boolean {
        return try {
            val ts  = (System.currentTimeMillis()/1000).toString()
            val sig = md5("${issue}&${betType}&${amount}&${ts}&R2Ks_5Fq")
            val body = JSONObject().apply {
                put("issueNumber", issue); put("typeId", typeId(gameKey))
                put("betType", betType); put("betAmount", amount)
                put("timestamp", ts); put("signature", sig)
            }.toString().toRequestBody("application/json".toMediaType())
            val r = client.newCall(Request.Builder().url("$BASE/api/webapi/PlaceBet")
                .post(body).addHeader("Authorization", jwtToken)
                .addHeader("Content-Type","application/json").build()).await()
            JSONObject(r.body?.string() ?: "{}").optInt("code") == 0
        } catch (e: Exception) { log("ERR","Bet: ${e.message}"); false }
    }

    private suspend fun settle(betType: String) {
        val prev = oldBal
        fetchBalance()
        val pl  = balance - prev
        val won = pl > 0
        sessionPL = balance - initBal
        if (won) { wins++; lastResult = "W"
            if (strategies[spStrategy.selectedItemPosition] == "Anti-Martingale")
                curBet = (curBet * 2).coerceAtMost(baseBet * 64) else curBet = baseBet
        } else { losses++; lastResult = "L"
            if (strategies[spStrategy.selectedItemPosition] == "Martingale")
                curBet = (curBet * 2).coerceAtMost(baseBet * 64) else curBet = baseBet
        }
        history.add(BetRecord(rounds,"",betType,curBet,won,pl,balance))
        val col = if (pl >= 0) "#10B981" else "#F43F5E"
        log("SETTLE","${if(won)"✅ WIN" else "❌ LOSS"}  P/L=₹%.2f  Bal=₹%.2f  Session=₹%.2f"
            .format(pl, balance, sessionPL))
        runOnUiThread {
            tvWins.text = wins.toString(); tvLosses.text = losses.toString()
            val s = "%.2f".format(sessionPL)
            tvPL.text = if (sessionPL >= 0) "+$s" else s
            tvPL.setTextColor(Color.parseColor(if (sessionPL >= 0) "#10B981" else "#F43F5E"))
        }
    }

    private fun showHistory() {
        if (history.isEmpty()) { toast("No history yet"); return }
        val sb = StringBuilder("# | Type | Amt | Result | P/L | Balance\n")
        sb.append("─────────────────────────────────────\n")
        history.reversed().take(40).forEach { r ->
            sb.append("#${r.round}  ${r.betType}  ₹${r.amount}  ${if(r.win)"WIN" else "LOSS"}  " +
                "${if(r.pl>=0)"+" else ""}${"%.2f".format(r.pl)}  ₹${"%.2f".format(r.balance)}\n")
        }
        AlertDialog.Builder(this).setTitle("📊 Bet History")
            .setMessage(sb.toString()).setPositiveButton("Close", null).show()
    }

    private fun showSettings() {
        val v = LayoutInflater.from(this).inflate(R.layout.dialog_settings, null, false)
        v.findViewById<EditText>(R.id.setTrig1).setText(trigSec1.toString())
        v.findViewById<EditText>(R.id.setTrig2).setText(trigSec2.toString())
        v.findViewById<EditText>(R.id.setFetch1).setText(fetchSec1.toString())
        v.findViewById<EditText>(R.id.setFetch2).setText(fetchSec2.toString())
        v.findViewById<EditText>(R.id.setBal1).setText(balSec1.toString())
        v.findViewById<EditText>(R.id.setBal2).setText(balSec2.toString())
        v.findViewById<EditText>(R.id.setSettle).setText(settleDly.toString())
        v.findViewById<EditText>(R.id.setProfit).setText(stopProfit.toString())
        v.findViewById<EditText>(R.id.setLoss).setText(stopLoss.toString())
        AlertDialog.Builder(this).setTitle("⚙️ Settings").setView(v)
            .setPositiveButton("Save") { _,_ ->
                trigSec1   = v.findViewById<EditText>(R.id.setTrig1).text.toString().toIntOrNull()    ?: trigSec1
                trigSec2   = v.findViewById<EditText>(R.id.setTrig2).text.toString().toIntOrNull()    ?: trigSec2
                fetchSec1  = v.findViewById<EditText>(R.id.setFetch1).text.toString().toIntOrNull()   ?: fetchSec1
                fetchSec2  = v.findViewById<EditText>(R.id.setFetch2).text.toString().toIntOrNull()   ?: fetchSec2
                balSec1    = v.findViewById<EditText>(R.id.setBal1).text.toString().toIntOrNull()     ?: balSec1
                balSec2    = v.findViewById<EditText>(R.id.setBal2).text.toString().toIntOrNull()     ?: balSec2
                settleDly  = v.findViewById<EditText>(R.id.setSettle).text.toString().toIntOrNull()   ?: settleDly
                stopProfit = v.findViewById<EditText>(R.id.setProfit).text.toString().toDoubleOrNull()?: stopProfit
                stopLoss   = v.findViewById<EditText>(R.id.setLoss).text.toString().toDoubleOrNull()  ?: stopLoss
                log("SET","Settings saved ✓")
            }.setNegativeButton("Cancel", null).show()
    }

    private fun typeId(k: String) = when { k=="30S"->30; k=="1MIN"->1; k=="3MIN"->3; else->5 }

    private fun md5(s: String): String =
        MessageDigest.getInstance("MD5").digest(s.toByteArray()).joinToString("") { "%02x".format(it) }

    private fun log(tag: String, msg: String) {
        val ts = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
        runOnUiThread {
            tvLog.append("[$ts] $tag: $msg\n")
            logScrollView.post { logScrollView.fullScroll(ScrollView.FOCUS_DOWN) }
        }
    }

    private fun toast(m: String) = runOnUiThread { Toast.makeText(this,m,Toast.LENGTH_SHORT).show() }

    private suspend fun Call.await(): Response = suspendCancellableCoroutine { cont ->
        enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) { cont.cancel(e) }
            override fun onResponse(call: Call, response: Response) { cont.resume(response) {} }
        })
    }
}
