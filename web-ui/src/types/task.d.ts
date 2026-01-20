// Based on the Pydantic model in the backend

export type TaskType = 'keyword_search' | 'seller_monitoring'

export interface Task {
  id: number;
  task_name: string;
  enabled: boolean;
  task_type: TaskType;
  keyword?: string | null;
  seller_id?: string | null;
  description: string;
  max_pages: number;
  max_products_per_run?: number | null;
  personal_only: boolean;
  min_price: string | null;
  max_price: string | null;
  cron: string | null;
  ai_prompt_base_file: string;
  ai_prompt_criteria_file: string;
  account_state_file?: string | null;
  free_shipping?: boolean;
  new_publish_option?: string | null;
  region?: string | null;
  is_public?: boolean;
  is_running: boolean;
}

// For PATCH requests, all fields are optional
export type TaskUpdate = Partial<Omit<Task, 'id'>>;

// For AI-driven task creation
export interface TaskGenerateRequest {
  task_name: string;
  task_type: TaskType;
  keyword?: string | null;
  seller_id?: string | null;
  description: string;
  personal_only?: boolean;
  min_price?: string | null;
  max_price?: string | null;
  max_pages?: number;
  max_products_per_run?: number | null;
  cron?: string | null;
  account_state_file?: string | null;
  free_shipping?: boolean;
  new_publish_option?: string | null;
  region?: string | null;
  is_public?: boolean;
}
