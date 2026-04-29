(function () {
  "use strict";

  function apiBase() {
    var raw = typeof window.__API_BASE__ === "string" ? window.__API_BASE__.trim() : "";
    return raw.replace(/\/+$/, "");
  }

  function emailToUserId(email) {
    return email.trim().toLowerCase();
  }

  function resolveContentType(file) {
    if (file.type && file.type.length > 0) {
      return file.type;
    }
    return "application/octet-stream";
  }

  function showError(message) {
    var el = document.getElementById("error-banner");
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function hideError() {
    document.getElementById("error-banner").classList.add("hidden");
  }

  function setSubmitting(busy) {
    var btn = document.getElementById("submit-btn");
    btn.disabled = !!busy;
    btn.textContent = busy ? "Working…" : "Upload & transcribe";
  }

  function showStatusPanel(show) {
    document.getElementById("status-panel").classList.toggle("hidden", !show);
  }

  function updateStatus(text, detail, jobId, transcriptUrl) {
    document.getElementById("status-message").textContent = text;
    var detailEl = document.getElementById("status-detail");
    if (detail) {
      detailEl.textContent = detail;
      detailEl.classList.remove("hidden");
    } else {
      detailEl.textContent = "";
      detailEl.classList.add("hidden");
    }
    var jobLine = document.getElementById("job-id-line");
    if (jobId) {
      jobLine.textContent = "Job ID: " + jobId;
      jobLine.classList.remove("hidden");
    } else {
      jobLine.classList.add("hidden");
    }
    var box = document.getElementById("transcript-url-box");
    var field = document.getElementById("transcript-url-field");
    var link = document.getElementById("transcript-open-link");
    var copyBtn = document.getElementById("transcript-copy-btn");
    if (transcriptUrl) {
      field.value = transcriptUrl;
      link.href = transcriptUrl;
      box.classList.remove("hidden");
      box.setAttribute("aria-hidden", "false");
    } else {
      field.value = "";
      link.removeAttribute("href");
      copyBtn.textContent = "Copy";
      box.classList.add("hidden");
      box.setAttribute("aria-hidden", "true");
    }
    showStatusPanel(true);
  }

  async function fetchJson(url, options) {
    var res = await fetch(url, options);
    var text = await res.text();
    var data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      /* ignore */
    }
    if (!res.ok) {
      var detail =
        data && typeof data.detail === "string"
          ? data.detail
          : text || res.statusText || "Request failed";
      throw new Error(detail);
    }
    return data;
  }

  var pollTimer = null;

  function stopPolling() {
    if (pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function fetchTranscriptUrl(base, jobId, userId) {
    var url =
      base +
      "/transcript/" +
      encodeURIComponent(jobId) +
      "?user_id=" +
      encodeURIComponent(userId);

    return fetchJson(url, { method: "GET" });
  }

  function pollStatus(base, jobId, userId) {
    stopPolling();
    var intervalMs = 5000;

    function tick() {
      fetchJson(base + "/status/" + encodeURIComponent(jobId), { method: "GET" })
        .then(function (data) {
          var status = data.status || "";
          var detail =
            status === "PENDING"
              ? "Waiting for worker…"
              : status === "PROCESSING"
                ? "Transcribing…"
                : "";
          updateStatus(status, detail, jobId, null);

          if (status === "SUCCESS") {
            stopPolling();
            updateStatus("Success", "Fetching transcript link...", jobId, null);
            fetchTranscriptUrl(base, jobId, userId)
              .then(function (transcriptData) {
                updateStatus(
                  "Success",
                  "Your transcript is ready.",
                  jobId,
                  transcriptData.transcript_url
                );
                setSubmitting(false);
              })
              .catch(function (err) {
                updateStatus(
                  "Success",
                  "Transcript completed, but the download URL could not be loaded: " +
                    (err.message || String(err)),
                  jobId,
                  null
                );
                setSubmitting(false);
              });
          } else if (status === "FAILED") {
            stopPolling();
            var err = data.error_message || data.errorMessage || "Unknown error";
            updateStatus("Failed", err, jobId, null);
            setSubmitting(false);
          }
        })
        .catch(function (err) {
          stopPolling();
          showError(err.message || String(err));
          setSubmitting(false);
        });
    }

    tick();
    pollTimer = setInterval(tick, intervalMs);
  }

  document.getElementById("transcript-copy-btn").addEventListener("click", function () {
    var field = document.getElementById("transcript-url-field");
    var btn = document.getElementById("transcript-copy-btn");
    var url = field && field.value;
    if (!url) return;
    function revert() {
      btn.textContent = "Copy";
    }
    function flash() {
      btn.textContent = "Copied!";
      setTimeout(revert, 1500);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(flash).catch(function () {
        field.focus();
        field.select();
        try {
          if (document.execCommand("copy")) flash();
        } catch (_) {}
      });
    } else {
      field.focus();
      field.select();
      try {
        if (document.execCommand("copy")) flash();
      } catch (_) {}
    }
  });

  document.getElementById("upload-form").addEventListener("submit", function (e) {
    e.preventDefault();
    hideError();
    stopPolling();

    var base = apiBase();
    if (!base) {
      showError(
        "Set window.__API_BASE__ in index.html (or inject at deploy time) to your API base URL."
      );
      return;
    }

    var emailInput = document.getElementById("email");
    var audioInput = document.getElementById("audio");
    var email = emailInput.value;
    var file = audioInput.files && audioInput.files[0];

    if (!email || !file) {
      showError("Please enter your email and choose an audio file.");
      return;
    }

    var userId = emailToUserId(email);
    var filename = file.name || "audio.bin";
    var contentType = resolveContentType(file);

    setSubmitting(true);
    updateStatus("Starting…", "Requesting upload URL…", null, null);

    fetchJson(base + "/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        user_id: userId,
        filename: filename,
        content_type: contentType,
      }),
    })
      .then(function (uploadResp) {
        var jobId = uploadResp.job_id;
        var uploadUrl = uploadResp.upload_url;
        var s3Key = uploadResp.s3_key;

        updateStatus("Uploading…", "Sending file to storage…", jobId, null);

        return fetch(uploadUrl, {
          method: "PUT",
          body: file,
          headers: { "Content-Type": contentType },
        }).then(function (putRes) {
          if (!putRes.ok) {
            throw new Error(
              "Upload to storage failed (" + putRes.status + "). Check Content-Type matches the file."
            );
          }
          var confirmUrl =
            base +
            "/upload/confirm/" +
            encodeURIComponent(jobId) +
            "?user_id=" +
            encodeURIComponent(userId) +
            "&s3_key=" +
            encodeURIComponent(s3Key);

          updateStatus("Confirming…", "Queueing transcription…", jobId, null);

          return fetchJson(confirmUrl, { method: "POST" }).then(function () {
            updateStatus("Queued", "Polling for completion…", jobId, null);
            pollStatus(base, jobId, userId);
          });
        });
      })
      .catch(function (err) {
        showError(err.message || String(err));
        setSubmitting(false);
      });
  });
})();
