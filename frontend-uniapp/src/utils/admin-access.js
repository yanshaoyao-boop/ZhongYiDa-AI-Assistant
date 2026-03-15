const ROOT_ROLES = new Set(['super_admin', 'owner'])
const SECTION_PERMISSION_MAP = {
	notices: 'edit_notices',
	staff: 'manage_staff',
	'chat-logs': 'view_logs',
	lab: 'edit_settings',
	knowledge: ['edit_knowledge', 'edit_prices', 'edit_cases'],
}

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

const normalizePermissions = (permissions) => {
	if (Array.isArray(permissions)) {
		return [...new Set(permissions.filter((item) => typeof item === 'string' && item.trim()))]
	}
	if (typeof permissions === 'string' && permissions.trim()) {
		try {
			return normalizePermissions(JSON.parse(permissions))
		} catch (error) {
			return []
		}
	}
	return []
}

export const getStoredUserPermissions = () => {
	return normalizePermissions(readStoredUser()?.permissions)
}

const isAdminRole = (role) => Boolean(role && role !== 'employee')

export const canAccessAdminSection = (section, role, options = {}) => {
	const userPermissions = options.permissions || getStoredUserPermissions()
	if (ROOT_ROLES.has(role)) return true

	if (section === 'admin') {
		return isAdminRole(role)
	}

	const requiredPermission = SECTION_PERMISSION_MAP[section]
	if (requiredPermission) {
		if (Array.isArray(requiredPermission)) {
			return requiredPermission.some((permission) => userPermissions.includes(permission))
		}
		return userPermissions.includes(requiredPermission)
	}

	return isAdminRole(role)
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
	const userPermissions = options.permissions || getStoredUserPermissions()
	const fallbackUrl = options.fallbackUrl || (canAccessAdminSection('admin', role, { permissions: userPermissions }) ? '/pages/admin/admin' : '/pages/chat/chat')

	if (canAccessAdminSection(section, role, { permissions: userPermissions })) {
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
