<template>
	<!-- #ifndef H5 -->
	<view class="mp-staff-page">
		<view class="admin-nav">
			<view class="nav-btn-circle" @tap="goBackToAdmin">
				<IconChevronLeft size="20" />
			</view>
			<text class="page-title">员工管理</text>
			<view style="width: 72rpx;"></view>
		</view>

		<view class="summary-row">
			<view class="card summary-item">
				<text class="muted">启用账号</text>
				<text class="title">{{ activeUserCount }}</text>
			</view>
			<view class="card summary-item">
				<text class="muted">分支机构</text>
				<text class="title">{{ structure.length }}</text>
			</view>
		</view>

		<view class="mp-staff-toolbar">
			<button class="btn primary" @tap="openCreateUserEditor">创建新用户</button>
			<button class="btn" :disabled="loading || actionLoading" @tap="fetchData">刷新列表</button>
			<button class="btn" :disabled="actionLoading || importExportLoading" @tap="handleExport">{{ importExportLoading ? '处理中...' : '导出 Excel' }}</button>
			<button class="btn" :disabled="actionLoading || importExportLoading" @tap="handleImport">{{ importExportLoading ? '处理中...' : '导入 Excel' }}</button>
			<button v-if="canManageStructure" class="btn" @tap="openStructureManager">机构管理</button>
		</view>

		<view v-if="actionMessage" :class="['card', 'feedback', actionType]">
			<text class="feedback-title">{{ actionType === 'error' ? '操作失败' : '操作成功' }}</text>
			<text class="muted">{{ actionMessage }}</text>
		</view>

		<view v-if="showUserEditor" class="mp-staff-editor-card">
			<view class="editor-header">
				<text class="section-title">{{ editorMode === 'edit' ? '编辑用户' : '创建用户' }}</text>
				<IconX size="18" color="#94a3b8" @tap="closeUserEditor" />
			</view>

			<view class="mp-editor-grid">
				<input v-model="userForm.username" class="field" placeholder="登录账号" :disabled="editorMode === 'edit'" />
				<input v-model="userForm.full_name" class="field" placeholder="真实姓名" />
				<input
					v-model="userForm.password"
					class="field"
					password
					:placeholder="editorMode === 'edit' ? '留空表示不修改密码' : '登录密码'"
				/>

				<picker :range="roleLabels" :value="selectedRoleIndex" @change="handleRoleChange">
					<view class="field">{{ currentRoleLabel }}</view>
				</picker>

				<picker :range="branchLabels" :value="selectedBranchIndex" @change="handleBranchChange">
					<view class="field">{{ currentBranchLabel }}</view>
				</picker>

				<picker :range="departmentLabels" :value="selectedDepartmentIndex" @change="handleDepartmentChange">
					<view class="field">{{ currentDepartmentLabel }}</view>
				</picker>

				<view class="wide-row">
					<text class="muted">账号状态</text>
					<switch :checked="userForm.is_active" @change="handleActiveChange" color="#2563eb" />
				</view>
			</view>

			<text v-if="roleHint" class="editor-hint">{{ roleHint }}</text>

			<view class="row">
				<button class="btn" @tap="closeUserEditor">取消</button>
				<button class="btn primary" :disabled="actionLoading" @tap="saveUser">
					{{ actionLoading ? '保存中...' : '确认保存' }}
				</button>
			</view>
		</view>

		<view v-if="showStructureManager" class="mp-staff-editor-card">
			<view class="editor-header">
				<text class="section-title">{{ auth.isSuperAdmin ? '分支与部门管理' : '本分支部门管理' }}</text>
				<IconX size="18" color="#94a3b8" @tap="closeStructureManager" />
			</view>

			<view class="mp-editor-grid">
				<view v-if="auth.isSuperAdmin" class="wide-row">
					<input v-model="newBranchName" class="field grow" placeholder="新分公司名称" />
					<button class="btn" :disabled="actionLoading" @tap="createBranch">添加分支</button>
				</view>

				<picker :range="branchLabels" :value="selectedStructureBranchIndex" @change="handleStructureBranchChange">
					<view class="field">{{ currentStructureBranchLabel }}</view>
				</picker>

				<view class="wide-row">
					<input v-model="newDeptName" class="field grow" placeholder="新部门名称" />
					<button class="btn" :disabled="actionLoading || !selectedStructureBranchId" @tap="createDepartment">添加部门</button>
				</view>

				<view class="wide-row wrap">
					<text v-if="structureDepartments.length === 0" class="muted">当前分支暂无部门</text>
					<view v-for="dept in structureDepartments" :key="dept.id" class="chip">{{ dept.name }}</view>
				</view>
			</view>
		</view>

		<view class="card">
			<input
				v-model="searchQuery"
				class="mp-staff-search"
				type="text"
				confirm-type="search"
				placeholder="搜索姓名、账号、分支或角色"
			/>
		</view>

		<scroll-view scroll-y class="list-scroll">
			<view v-if="loading" class="card center mp-staff-state">
				<text class="mp-staff-state-title">数据加载中</text>
				<text class="mp-staff-state-hint">正在拉取员工列表与组织架构...</text>
			</view>
			<view v-else-if="errorMsg" class="card center mp-staff-state">
				<text class="mp-staff-state-title error-text">加载失败</text>
				<text class="mp-staff-state-hint">{{ errorMsg }}</text>
			</view>
			<view v-else-if="filteredUsers.length === 0" class="card center mp-staff-state">
				<text class="mp-staff-state-title">没有找到匹配员工</text>
				<text class="mp-staff-state-hint">试试更换搜索关键字。</text>
			</view>

			<view v-for="user in filteredUsers" :key="user.id" class="card user-card">
				<view class="user-head">
					<view>
						<text class="section-title">{{ user.full_name || user.username }}</text>
						<text class="muted">账号：{{ user.username }}</text>
					</view>
					<text class="chip">{{ roleMap[user.role] || user.role }}</text>
				</view>

				<view class="user-meta-lines">
					<text class="muted">分支：{{ user.branch || '未分配' }}</text>
					<text class="muted">部门：{{ user.department || '未分配' }}</text>
					<text :class="['status-tag', user.is_active ? 'active' : 'disabled']">
						{{ user.is_active ? '正常' : '已禁用' }}
					</text>
				</view>

				<view class="row toolbar">
					<button class="mp-staff-action" @tap="openEditUserEditor(user)">修改</button>
					<button class="mp-staff-action danger" :disabled="user.username === currentUserName" @tap="confirmDeleteUser(user)">删除</button>
				</view>
			</view>
		</scroll-view>
	</view>
	<!-- #endif -->
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
// #ifdef H5
import axios from 'axios'
// #endif
import { resolveApiUrl } from '@/utils/api'
import { ensureAdminPageAccess } from '@/utils/admin-access'
import { useAuthStore } from '@/store/auth'
import { ChevronLeft as IconChevronLeft, X as IconX } from 'lucide-vue-next'

const roleMap = {
	owner: '老板',
	executive: '高管',
	daily_admin: '日常管理员',
	staff_admin: '普通管理员',
	employee: '员工',
	super_admin: '超级管理员',
	branch_admin: '分支管理员',
	user: '普通员工',
}

const auth = useAuthStore()
const users = ref([])
const structure = ref([])
const searchQuery = ref('')
const loading = ref(false)
const errorMsg = ref('')
const actionLoading = ref(false)
const importExportLoading = ref(false)
const actionMessage = ref('')
const actionType = ref('success')
const showUserEditor = ref(false)
const showStructureManager = ref(false)
const editorMode = ref('create')
const editingUserId = ref(null)
const selectedStructureBranchId = ref(null)
const newBranchName = ref('')
const newDeptName = ref('')

const createEmptyUserForm = () => ({
	username: '',
	full_name: '',
	password: '',
	role: 'employee',
	branch_id: null,
	department_id: null,
	is_active: true,
})

const userForm = ref(createEmptyUserForm())

const filteredUsers = computed(() => {
	if (!searchQuery.value.trim()) return users.value
	const keyword = searchQuery.value.trim().toLowerCase()
	return users.value.filter((user) => {
		return [user.username, user.full_name, user.branch, user.department, roleMap[user.role]].some((value) =>
			String(value || '').toLowerCase().includes(keyword)
		)
	})
})

const activeUserCount = computed(() => users.value.filter((user) => user.is_active).length)
const currentUserName = computed(() => auth.user?.username || '')
const canManageStructure = computed(() => auth.isAdmin)
const roleOptions = computed(() => {
	const base = [
		{ label: '员工', value: 'employee' },
		{ label: '普通管理员', value: 'staff_admin' },
		{ label: '日常管理员', value: 'daily_admin' },
	]
	if (auth.isSuperAdmin) {
		base.push({ label: '高管', value: 'executive' })
		base.push({ label: '老板', value: 'owner' })
	}
	return base
})
const roleLabels = computed(() => roleOptions.value.map((item) => item.label))
const branchOptions = computed(() => structure.value.map((item) => ({ label: item.name, value: item.id })))
const branchLabels = computed(() => branchOptions.value.map((item) => item.label))
const availableDepartments = computed(() => {
	const branch = structure.value.find((item) => item.id === userForm.value.branch_id)
	return branch?.departments || []
})
const departmentLabels = computed(() => availableDepartments.value.map((item) => item.name))
const structureDepartments = computed(() => {
	const branch = structure.value.find((item) => item.id === selectedStructureBranchId.value)
	return branch?.departments || []
})
const selectedRoleIndex = computed(() => Math.max(roleOptions.value.findIndex((item) => item.value === userForm.value.role), 0))
const selectedBranchIndex = computed(() => {
	const index = branchOptions.value.findIndex((item) => item.value === userForm.value.branch_id)
	return Math.max(index, 0)
})
const selectedDepartmentIndex = computed(() => {
	const index = availableDepartments.value.findIndex((item) => item.id === userForm.value.department_id)
	return Math.max(index, 0)
})
const selectedStructureBranchIndex = computed(() => {
	const index = branchOptions.value.findIndex((item) => item.value === selectedStructureBranchId.value)
	return Math.max(index, 0)
})
const currentRoleLabel = computed(() => roleOptions.value[selectedRoleIndex.value]?.label || '选择角色')
const currentBranchLabel = computed(() => {
	if (!branchOptions.value.length) return '暂无可用分支'
	return branchOptions.value[selectedBranchIndex.value]?.label || '选择分支'
})
const currentDepartmentLabel = computed(() => {
	if (!availableDepartments.value.length) return '无可用部门（可选）'
	return availableDepartments.value[selectedDepartmentIndex.value]?.name || '选择部门'
})
const currentStructureBranchLabel = computed(() => {
	if (!branchOptions.value.length) return '暂无可管理分支'
	return branchOptions.value[selectedStructureBranchIndex.value]?.label || '选择分支'
})
const roleHint = computed(() => {
	if (auth.isSuperAdmin) {
		return '前端只做权限提示，最终权限仍以后端为准。'
	}
	return '分支管理员只能管理本分支账号，不能赋予超级管理员角色。'
})

const setActionFeedback = (message, type = 'success') => {
	actionMessage.value = message
	actionType.value = type
}

const getTokenHeaders = () => {
	try {
		const token = uni.getStorageSync('token')
		return token ? { Authorization: `Bearer ${token}` } : {}
	} catch (error) {
		return {}
	}
}

const extractErrorMessage = (error, fallback) => {
	// #ifdef H5
	return error?.response?.data?.detail || error?.message || fallback
	// #endif
	return error?.message || fallback
}

const setBranchAndDepartment = (branchId, preferredDepartmentId = null) => {
	userForm.value.branch_id = branchId
	const branch = structure.value.find((item) => item.id === branchId)
	const departments = branch?.departments || []
	if (!departments.length) {
		userForm.value.department_id = null
		return
	}
	const matched = departments.find((item) => item.id === preferredDepartmentId)
	userForm.value.department_id = matched?.id || departments[0].id
}

const syncEditorDefaults = () => {
	if (!structure.value.length) return

	if (!selectedStructureBranchId.value) {
		selectedStructureBranchId.value = auth.isSuperAdmin ? structure.value[0].id : auth.user?.branch_id || structure.value[0].id
	}

	if (!userForm.value.branch_id) {
		const defaultBranchId = auth.isSuperAdmin ? structure.value[0].id : auth.user?.branch_id || structure.value[0].id
		setBranchAndDepartment(defaultBranchId)
	}
}

const requestStaff = async (path, options = {}) => {
	const url = resolveApiUrl(path)
	const method = options.method || 'GET'

	// #ifdef H5
	const response = await axios({
		url,
		method,
		data: options.data,
		headers: {
			...getTokenHeaders(),
			...(options.headers || {}),
		},
	})
	return response.data
	// #endif

	// #ifndef H5
	return await new Promise((resolve, reject) => {
		uni.request({
			url,
			method,
			data: options.data,
			header: {
				'content-type': 'application/json',
				...getTokenHeaders(),
				...(options.headers || {}),
			},
			timeout: 15000,
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data)
					return
				}
				const detail = res.data && typeof res.data === 'object' ? res.data.detail : ''
				reject(new Error(detail || `request failed (${res.statusCode})`))
			},
			fail: (error) => reject(error),
		})
	})
	// #endif
}

const uploadStaffImportFile = async (filePath) => {
	return await new Promise((resolve, reject) => {
		uni.uploadFile({
			url: resolveApiUrl('/api/staff/users/import'),
			filePath,
			name: 'file',
			header: readToken() ? { Authorization: `Bearer ${readToken()}` } : {},
			success: (result) => {
				try {
					resolve(JSON.parse(result.data || '{}'))
				} catch (error) {
					reject(new Error('导入响应解析失败'))
				}
			},
			fail: (error) => reject(error),
		})
	})
}

const readToken = () => {
	try {
		return uni.getStorageSync('token')
	} catch (error) {
		return ''
	}
}

const fetchData = async () => {
	loading.value = true
	errorMsg.value = ''
	try {
		const [userData, structureData] = await Promise.all([
			requestStaff('/api/staff/users'),
			requestStaff('/api/staff/structure'),
		])
		users.value = Array.isArray(userData) ? userData : []
		structure.value = Array.isArray(structureData) ? structureData : []
		syncEditorDefaults()
	} catch (error) {
		errorMsg.value = extractErrorMessage(error, '加载员工数据失败')
	} finally {
		loading.value = false
	}
}

const openCreateUserEditor = () => {
	showStructureManager.value = false
	showUserEditor.value = true
	editorMode.value = 'create'
	editingUserId.value = null
	userForm.value = createEmptyUserForm()
	syncEditorDefaults()
}

const openEditUserEditor = (user) => {
	showStructureManager.value = false
	showUserEditor.value = true
	editorMode.value = 'edit'
	editingUserId.value = user.id
	userForm.value = {
		username: user.username,
		full_name: user.full_name || '',
		password: '',
		role: user.role,
		branch_id: user.branch_id,
		department_id: user.department_id,
		is_active: Boolean(user.is_active),
	}
	syncEditorDefaults()
}

const closeUserEditor = () => {
	showUserEditor.value = false
}

const openStructureManager = () => {
	showUserEditor.value = false
	showStructureManager.value = true
	syncEditorDefaults()
}

const closeStructureManager = () => {
	showStructureManager.value = false
}

const validateUserForm = () => {
	if (!userForm.value.username.trim()) throw new Error('请输入登录账号')
	if (!userForm.value.full_name.trim()) throw new Error('请输入真实姓名')
	if (editorMode.value === 'create' && !userForm.value.password.trim()) throw new Error('请输入初始密码')
	if (!userForm.value.branch_id) throw new Error('请选择所属分支')
}

const saveUser = async () => {
	try {
		validateUserForm()
	} catch (error) {
		setActionFeedback(error.message || '表单校验失败', 'error')
		return
	}

	actionLoading.value = true
	try {
		const payload = {
			username: userForm.value.username.trim(),
			full_name: userForm.value.full_name.trim(),
			password: userForm.value.password.trim(),
			role: userForm.value.role,
			branch_id: userForm.value.branch_id,
			department_id: userForm.value.department_id,
			is_active: userForm.value.is_active,
		}

		if (editingUserId.value) {
			const updatePayload = { ...payload }
			if (!updatePayload.password) delete updatePayload.password
			delete updatePayload.username
			await requestStaff(`/api/staff/users/${editingUserId.value}`, {
				method: 'PATCH',
				data: updatePayload,
			})
			setActionFeedback('用户信息已更新')
		} else {
			await requestStaff('/api/staff/users', {
				method: 'POST',
				data: payload,
			})
			setActionFeedback('用户已创建')
		}

		await fetchData()
		showUserEditor.value = false
	} catch (error) {
		setActionFeedback(extractErrorMessage(error, '保存用户失败'), 'error')
	} finally {
		actionLoading.value = false
	}
}

const confirmDeleteUser = (user) => {
	if (user.username === currentUserName.value) {
		setActionFeedback('当前登录账号不能在这里删除', 'error')
		return
	}

	uni.showModal({
		title: '删除用户',
		content: `确定删除 ${user.full_name || user.username} 吗？`,
		success: async ({ confirm }) => {
			if (!confirm) return
			actionLoading.value = true
			try {
				await requestStaff(`/api/staff/users/${user.id}`, {
					method: 'DELETE',
				})
				setActionFeedback('用户已删除')
				await fetchData()
			} catch (error) {
				setActionFeedback(extractErrorMessage(error, '删除用户失败'), 'error')
			} finally {
				actionLoading.value = false
			}
		},
	})
}

const createBranch = async () => {
	if (!newBranchName.value.trim()) {
		setActionFeedback('请输入分支名称', 'error')
		return
	}
	actionLoading.value = true
	try {
		await requestStaff('/api/staff/branches', {
			method: 'POST',
			data: { name: newBranchName.value.trim() },
		})
		newBranchName.value = ''
		setActionFeedback('分支已创建')
		await fetchData()
	} catch (error) {
		setActionFeedback(extractErrorMessage(error, '创建分支失败'), 'error')
	} finally {
		actionLoading.value = false
	}
}

const createDepartment = async () => {
	if (!selectedStructureBranchId.value || !newDeptName.value.trim()) {
		setActionFeedback('请选择分支并填写部门名称', 'error')
		return
	}
	actionLoading.value = true
	try {
		await requestStaff('/api/staff/departments', {
			method: 'POST',
			data: {
				name: newDeptName.value.trim(),
				branch_id: selectedStructureBranchId.value,
			},
		})
		newDeptName.value = ''
		setActionFeedback('部门已创建')
		await fetchData()
	} catch (error) {
		setActionFeedback(extractErrorMessage(error, '创建部门失败'), 'error')
	} finally {
		actionLoading.value = false
	}
}

const handleImport = async () => {
	if (importExportLoading.value) return
	importExportLoading.value = true
	try {
		const chooseResult = await new Promise((resolve, reject) => {
			uni.chooseMessageFile({
				count: 1,
				type: 'file',
				success: resolve,
				fail: reject,
			})
		})
		const targetFile = chooseResult.tempFiles?.[0]
		if (!targetFile?.path) return

		const result = await uploadStaffImportFile(targetFile.path)
		const detailMessage = result.errors?.length ? `${result.message}；失败 ${result.errors.length} 条` : result.message || '导入完成'
		setActionFeedback(detailMessage)
		await fetchData()
		uni.showToast({ title: '导入完成', icon: 'success' })
	} catch (error) {
		setActionFeedback(extractErrorMessage(error, '导入失败'), 'error')
	} finally {
		importExportLoading.value = false
	}
}

const handleExport = async () => {
	if (importExportLoading.value) return
	importExportLoading.value = true
	try {
		const downloadResult = await new Promise((resolve, reject) => {
			uni.downloadFile({
				url: resolveApiUrl('/api/staff/users/export'),
				header: readToken() ? { Authorization: `Bearer ${readToken()}` } : {},
				success: resolve,
				fail: reject,
			})
		})

		if (downloadResult.statusCode < 200 || downloadResult.statusCode >= 300) {
			throw new Error(`导出失败 (${downloadResult.statusCode})`)
		}

		await new Promise((resolve, reject) => {
			uni.openDocument({
				filePath: downloadResult.tempFilePath,
				showMenu: true,
				success: resolve,
				fail: reject,
			})
		})
		setActionFeedback('导出文件已生成')
	} catch (error) {
		setActionFeedback(extractErrorMessage(error, '导出失败'), 'error')
	} finally {
		importExportLoading.value = false
	}
}

const handleRoleChange = (event) => {
	userForm.value.role = roleOptions.value[Number(event.detail.value)]?.value || 'user'
}

const handleBranchChange = (event) => {
	const branchId = branchOptions.value[Number(event.detail.value)]?.value || null
	setBranchAndDepartment(branchId)
}

const handleDepartmentChange = (event) => {
	userForm.value.department_id = availableDepartments.value[Number(event.detail.value)]?.id || null
}

const handleActiveChange = (event) => {
	userForm.value.is_active = Boolean(event.detail.value)
}

const handleStructureBranchChange = (event) => {
	selectedStructureBranchId.value = branchOptions.value[Number(event.detail.value)]?.value || null
}

const goBackToAdmin = () => {
	const pages = getCurrentPages()
	if (pages.length > 1) {
		uni.navigateBack({ delta: 1 })
		return
	}
	uni.navigateTo({ url: '/pages/admin/admin' })
}

// #ifdef H5
const importInput = ref(null)
const openUserModal = (user) => {
	if (user) {
		openEditUserEditor(user)
		return
	}
	openCreateUserEditor()
}
const openOrgModal = () => {
	openStructureManager()
}
const triggerImport = () => importInput.value && importInput.value.click()
const handleImportH5 = () => {}
const handleExportH5 = () => {
	window.open(resolveApiUrl('/api/staff/users/export'), '_blank')
}
// #endif

onMounted(() => {
	if (!ensureAdminPageAccess('staff')) return
	fetchData()
})
</script>

<style scoped>
.mp-staff-page {
	min-height: 100vh;
	padding: 24rpx;
	padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
	background: #f3f6fb;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	box-sizing: border-box;
}

.admin-nav {
	padding-top: calc(20rpx + env(safe-area-inset-top));
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.nav-btn-circle {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background: rgba(255, 255, 255, 0.96);
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.06);
}

.page-title {
	font-size: 38rpx;
	font-weight: 700;
	color: #0f172a;
}

.card,
.mp-staff-toolbar,
.mp-staff-editor-card {
	background: rgba(255, 255, 255, 0.96);
	border-radius: 28rpx;
	padding: 24rpx;
	box-shadow: 0 12rpx 30rpx rgba(15, 23, 42, 0.06);
}

.title,
.section-title {
	display: block;
	font-size: 32rpx;
	font-weight: 700;
	color: #0f172a;
}

.muted {
	display: block;
	font-size: 24rpx;
	line-height: 1.5;
	color: #64748b;
}

.summary-row,
.row,
.wide-row {
	display: flex;
	gap: 12rpx;
	align-items: center;
}

.summary-item {
	flex: 1;
}

.mp-staff-toolbar {
	display: flex;
	gap: 12rpx;
	flex-wrap: wrap;
}

.btn,
.mp-staff-action {
	margin: 0;
	min-height: 72rpx;
	padding: 0 24rpx;
	border-radius: 18rpx;
	background: #eef2ff;
	color: #1d4ed8;
	font-size: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.btn.primary {
	background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
	color: #fff;
}

.feedback.success {
	background: #eff6ff;
}

.feedback.error {
	background: #fff1f2;
}

.feedback-title {
	font-size: 26rpx;
	font-weight: 700;
	color: #0f172a;
	margin-bottom: 8rpx;
	display: block;
}

.mp-staff-editor-card {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.editor-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.mp-editor-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 12rpx;
}

.field,
.mp-staff-search {
	min-height: 76rpx;
	padding: 0 20rpx;
	border-radius: 18rpx;
	background: #f8fafc;
	display: flex;
	align-items: center;
	box-sizing: border-box;
	font-size: 26rpx;
	color: #0f172a;
}

.grow {
	flex: 1;
}

.editor-hint {
	font-size: 22rpx;
	line-height: 1.6;
	color: #64748b;
}

.chip {
	padding: 8rpx 14rpx;
	border-radius: 999rpx;
	background: #eff6ff;
	color: #1d4ed8;
	font-size: 22rpx;
}

.wrap {
	flex-wrap: wrap;
}

.list-scroll {
	flex: 1;
	min-height: 0;
}

.center {
	display: flex;
	align-items: center;
	justify-content: center;
	min-height: 140rpx;
}

.mp-staff-state {
	flex-direction: column;
	gap: 10rpx;
	text-align: center;
}

.mp-staff-state-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-staff-state-hint {
	font-size: 24rpx;
	line-height: 1.5;
	color: #64748b;
}

.error-text {
	color: #b91c1c;
}

.user-card {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-bottom: 16rpx;
}

.user-head {
	display: flex;
	justify-content: space-between;
	gap: 12rpx;
}

.user-meta-lines {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.status-tag {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 8rpx 16rpx;
	border-radius: 999rpx;
	font-size: 22rpx;
	font-weight: 600;
	width: fit-content;
}

.status-tag.active {
	background: #ecfdf5;
	color: #15803d;
}

.status-tag.disabled {
	background: #fef2f2;
	color: #dc2626;
}

.toolbar {
	justify-content: flex-end;
}

.mp-staff-action.danger {
	background: #fef2f2;
	color: #dc2626;
}

@media (max-width: 720px) {
	.mp-editor-grid {
		grid-template-columns: 1fr;
	}

	.summary-row,
	.row,
	.wide-row {
		flex-direction: column;
		align-items: stretch;
	}
}
</style>
