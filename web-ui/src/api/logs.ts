import { http } from '@/lib/http'

export async function getLogs(fromPos: number = 0): Promise<{ new_content: string; new_pos: number }> {
  return await http('/api/logs', { params: { from_pos: fromPos } })
}

export async function clearLogs(): Promise<void> {
  await http('/api/logs', { method: 'DELETE' })
}
