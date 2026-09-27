// Optional Supabase browser client for telemetry sync and cloud storage
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || ''

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseKey)

export async function getSupabase() {
  if (!isSupabaseConfigured) return null
  try {
    const { createClient } = await import('@supabase/supabase-js')
    return createClient(supabaseUrl, supabaseKey)
  } catch (err) {
    console.warn('Supabase SDK not loaded in browser environment:', err)
    return null
  }
}
