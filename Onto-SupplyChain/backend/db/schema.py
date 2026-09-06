from __future__ import annotations

from pathlib import Path

from db.database import connection_scope


SCHEMA_SQL = """
DROP TABLE IF EXISTS scenario_conversation_notes;
DROP TABLE IF EXISTS demo_scenarios;
DROP TABLE IF EXISTS atp_commitments;
DROP TABLE IF EXISTS routing_alternatives;
DROP TABLE IF EXISTS routing_operations;
DROP TABLE IF EXISTS routings;
DROP TABLE IF EXISTS item_suppliers;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS bom_alternatives;
DROP TABLE IF EXISTS bom_items;
DROP TABLE IF EXISTS bom_headers;
DROP TABLE IF EXISTS inventory_inbound;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS operation_dependencies;
DROP TABLE IF EXISTS operations;
DROP TABLE IF EXISTS production_orders;
DROP TABLE IF EXISTS work_center_calendar;
DROP TABLE IF EXISTS work_centers;
DROP TABLE IF EXISTS customer_orders;
DROP TABLE IF EXISTS finished_items;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  customer_name TEXT NOT NULL,
  priority_level TEXT NOT NULL,
  penalty_threshold_days INTEGER NOT NULL,
  penalty_rate REAL NOT NULL,
  delivery_reliability REAL NOT NULL,
  complaint_sensitivity TEXT NOT NULL
);

CREATE TABLE finished_items (
  item_id TEXT PRIMARY KEY,
  item_name TEXT NOT NULL,
  item_category TEXT NOT NULL,
  safety_stock REAL NOT NULL,
  min_order_quantity REAL NOT NULL,
  lot_size_rule TEXT NOT NULL,
  abc_classification TEXT NOT NULL
);

CREATE TABLE customer_orders (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  quantity REAL NOT NULL,
  requested_date TEXT NOT NULL,
  committed_date TEXT NOT NULL,
  order_priority INTEGER NOT NULL,
  order_type TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY(item_id) REFERENCES finished_items(item_id)
);

CREATE TABLE work_centers (
  wc_id TEXT PRIMARY KEY,
  wc_name TEXT NOT NULL,
  wc_type TEXT NOT NULL,
  plant_id TEXT NOT NULL,
  standard_capacity_per_day REAL NOT NULL,
  efficiency_factor REAL NOT NULL,
  overtime_capacity_per_day REAL NOT NULL,
  bottleneck_flag INTEGER NOT NULL,
  utilization_target REAL NOT NULL
);

CREATE TABLE work_center_calendar (
  calendar_id TEXT PRIMARY KEY,
  wc_id TEXT NOT NULL,
  work_date TEXT NOT NULL,
  available_hours REAL NOT NULL,
  maintenance_hours REAL NOT NULL,
  overtime_hours REAL NOT NULL,
  FOREIGN KEY(wc_id) REFERENCES work_centers(wc_id)
);

CREATE TABLE production_orders (
  wo_id TEXT PRIMARY KEY,
  order_id TEXT,
  item_id TEXT NOT NULL,
  planned_quantity REAL NOT NULL,
  confirmed_quantity REAL NOT NULL,
  planned_start TEXT NOT NULL,
  planned_end TEXT NOT NULL,
  actual_start TEXT,
  actual_end TEXT,
  forecast_end TEXT NOT NULL,
  priority INTEGER NOT NULL,
  status TEXT NOT NULL,
  delay_risk_score REAL NOT NULL,
  FOREIGN KEY(order_id) REFERENCES customer_orders(order_id),
  FOREIGN KEY(item_id) REFERENCES finished_items(item_id)
);

CREATE TABLE operations (
  op_id TEXT PRIMARY KEY,
  wo_id TEXT NOT NULL,
  op_sequence INTEGER NOT NULL,
  op_name TEXT NOT NULL,
  wc_id TEXT NOT NULL,
  setup_time_hours REAL NOT NULL,
  process_time_per_unit_hours REAL NOT NULL,
  queue_time_hours REAL NOT NULL,
  move_time_hours REAL NOT NULL,
  completion_percentage REAL NOT NULL,
  parallel_flag INTEGER NOT NULL,
  quality_hold_flag INTEGER NOT NULL,
  FOREIGN KEY(wo_id) REFERENCES production_orders(wo_id),
  FOREIGN KEY(wc_id) REFERENCES work_centers(wc_id)
);

CREATE TABLE operation_dependencies (
  id TEXT PRIMARY KEY,
  op_id TEXT NOT NULL,
  predecessor_op_id TEXT NOT NULL,
  overlap_percentage REAL NOT NULL,
  FOREIGN KEY(op_id) REFERENCES operations(op_id),
  FOREIGN KEY(predecessor_op_id) REFERENCES operations(op_id)
);

CREATE TABLE inventory (
  inventory_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  plant_id TEXT NOT NULL,
  storage_location TEXT NOT NULL,
  on_hand_qty REAL NOT NULL,
  in_transit_qty REAL NOT NULL,
  reserved_qty REAL NOT NULL,
  available_qty REAL NOT NULL,
  reorder_point REAL NOT NULL,
  last_updated TEXT NOT NULL,
  data_source TEXT NOT NULL
);

CREATE TABLE inventory_inbound (
  inbound_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  expected_arrival_date TEXT NOT NULL,
  quantity REAL NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE bom_headers (
  bom_id TEXT PRIMARY KEY,
  bom_version TEXT NOT NULL,
  parent_item_id TEXT NOT NULL,
  effective_from TEXT NOT NULL,
  effective_to TEXT,
  FOREIGN KEY(parent_item_id) REFERENCES finished_items(item_id)
);

CREATE TABLE bom_items (
  bom_item_id TEXT PRIMARY KEY,
  bom_id TEXT NOT NULL,
  child_item_id TEXT NOT NULL,
  level INTEGER NOT NULL,
  quantity_per REAL NOT NULL,
  scrap_factor REAL NOT NULL,
  phantom_flag INTEGER NOT NULL,
  purchase_or_make TEXT NOT NULL,
  FOREIGN KEY(bom_id) REFERENCES bom_headers(bom_id)
);

CREATE TABLE bom_alternatives (
  alt_id TEXT PRIMARY KEY,
  bom_item_id TEXT NOT NULL,
  alt_item_id TEXT NOT NULL,
  usage_priority INTEGER NOT NULL,
  substitution_ratio REAL NOT NULL,
  approval_status TEXT NOT NULL,
  FOREIGN KEY(bom_item_id) REFERENCES bom_items(bom_item_id)
);

CREATE TABLE suppliers (
  supplier_id TEXT PRIMARY KEY,
  supplier_name TEXT NOT NULL,
  supplier_tier TEXT NOT NULL,
  standard_lt_days INTEGER NOT NULL,
  rush_lt_days INTEGER NOT NULL,
  lt_variability REAL NOT NULL,
  moq REAL NOT NULL,
  capacity_limit REAL NOT NULL,
  on_time_rate REAL NOT NULL,
  quality_pass_rate REAL NOT NULL,
  average_delay_days REAL NOT NULL,
  geo_risk_level TEXT NOT NULL,
  single_source_flag INTEGER NOT NULL
);

CREATE TABLE item_suppliers (
  id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL,
  is_primary INTEGER NOT NULL,
  FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE routings (
  routing_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  routing_version TEXT NOT NULL,
  routing_type TEXT NOT NULL,
  total_lead_time_days REAL NOT NULL,
  bottleneck_wc_id TEXT NOT NULL,
  min_batch_size REAL NOT NULL,
  max_batch_size REAL NOT NULL,
  FOREIGN KEY(item_id) REFERENCES finished_items(item_id),
  FOREIGN KEY(bottleneck_wc_id) REFERENCES work_centers(wc_id)
);

CREATE TABLE routing_operations (
  routing_op_id TEXT PRIMARY KEY,
  routing_id TEXT NOT NULL,
  op_sequence INTEGER NOT NULL,
  wc_id TEXT NOT NULL,
  standard_setup_hours REAL NOT NULL,
  standard_process_hours REAL NOT NULL,
  FOREIGN KEY(routing_id) REFERENCES routings(routing_id),
  FOREIGN KEY(wc_id) REFERENCES work_centers(wc_id)
);

CREATE TABLE routing_alternatives (
  id TEXT PRIMARY KEY,
  routing_id TEXT NOT NULL,
  alternative_routing_id TEXT NOT NULL,
  applicability_condition TEXT NOT NULL,
  FOREIGN KEY(routing_id) REFERENCES routings(routing_id),
  FOREIGN KEY(alternative_routing_id) REFERENCES routings(routing_id)
);

CREATE TABLE atp_commitments (
  commitment_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  commitment_version INTEGER NOT NULL,
  committed_date TEXT NOT NULL,
  commitment_type TEXT NOT NULL,
  confidence_score REAL NOT NULL,
  risk_level TEXT NOT NULL,
  reason_chain_json TEXT NOT NULL,
  cost_impact REAL NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  actual_delivery_date TEXT,
  deviation_days INTEGER,
  FOREIGN KEY(order_id) REFERENCES customer_orders(order_id)
);

CREATE TABLE demo_scenarios (
  scenario_id TEXT PRIMARY KEY,
  scenario_code TEXT UNIQUE NOT NULL,
  scenario_name TEXT NOT NULL,
  scenario_type TEXT NOT NULL,
  user_prompt TEXT NOT NULL,
  target_order_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  is_default INTEGER NOT NULL,
  FOREIGN KEY(target_order_id) REFERENCES customer_orders(order_id)
);

CREATE TABLE scenario_conversation_notes (
  note_id TEXT PRIMARY KEY,
  scenario_code TEXT NOT NULL,
  note_type TEXT NOT NULL,
  note_text TEXT NOT NULL
);
"""


def initialize_database(db_path: Path | None = None) -> None:
    with connection_scope(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
