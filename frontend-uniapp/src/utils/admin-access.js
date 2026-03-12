const ADMIN_ROLES = new Set(['super_admin', 'branch_admin'])
const SUPER_ADMIN_ONLY_SECTIONS = new Set(['chat-logs', 'lab'])

const readStoredUser = () => {
	try {
		const rawUser = uni.getStorageSync('user')
		if (!rawUser) return null
		return typeof rawUser === 'string' ? JSON.parse(rawUser) : rawUser
	} catch (error) {
		return null
	}
}

export const getStoredUserRole = () => readStoredUser()?.role || ''

export const canAccessAdminSection = (section, role) => {
	if (!ADMIN_ROLES.has(role)) return false
	if (SUPER_ADMIN_ONLY_SECTIONS.has(section)) {
		return role === 'super_admin'
	}
	return ['admin', 'staff'].includes(section)
}

const redirectAfterDenied = (role, section, fallbackUrl) => {
	if (!role) {
		uni.reLaunch({ url: '/pages/login/login' })
		return
	}

	uni.reLaunch({ url: fallbackUrl })
}

export const ensureAdminPageAccess = (section, options = {}) => {
	const role = options.role || getStoredUserRole()
	const fallbackUrl = options.fallbackUrl || (ADMIN_ROLES.has(role) ? '/pages/admin/admin' : '/pages/chat/chat')

	if (canAccessAdminSection(section, role)) {
		return true
	}

	if (options.toast !== false) {
		uni.showToast({ title: '当前账号无权访问该页面', icon: 'none' })
	}

	if (options.redirect !== false) {
		setTimeout(() => {
			redirectAfterDenied(role, section, fallbackUrl)
		}, 80)
	}

	return false
}
