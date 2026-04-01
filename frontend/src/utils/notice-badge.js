export function getLatestNoticeId(notices) {
    if (!Array.isArray(notices) || notices.length === 0) {
        return null
    }

    let latestId = null
    for (const notice of notices) {
        const numericId = Number(notice?.id)
        if (!Number.isFinite(numericId)) {
            continue
        }
        latestId = latestId === null ? numericId : Math.max(latestId, numericId)
    }

    return latestId
}

export function hasUnreadNotices(notices, seenNoticeId) {
    const latestNoticeId = getLatestNoticeId(notices)
    if (latestNoticeId === null) {
        return false
    }

    const numericSeenId = Number(seenNoticeId)
    if (!Number.isFinite(numericSeenId)) {
        return true
    }

    return latestNoticeId > numericSeenId
}
