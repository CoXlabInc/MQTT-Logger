function strip_log_prefix(tag, ts, record)
    if record["topic"] and type(record["topic"]) == "string" then
        record["topic"] = record["topic"]:gsub("^log/", "")
    end
    record["body"] = (record["timestamp"] or "") .. " | " .. (record["msg"] or "")
    record["msg"] = nil
    record["timestamp"] = nil
    record["device"] = nil
    return 1, ts, record
end
