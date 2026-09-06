export interface UserProfile {
  id: number;
  username: string;
  displayName: string;
}

export interface NavigationNode {
  id: string;
  label: string;
  icon?: string;
  type?: 'category' | 'leaf';
  action?: 'open_tab' | 'link';
  payload?: string;
  children?: NavigationNode[];
}

export interface PageRegistrySection {
  id: string;
  title?: string;
  layout?: string;
  component?: string;
  fields?: string[];
  columns?: string[];
  filters?: string[];
  result_columns?: string[];
  row_actions?: string[];
  toolbar_actions?: string[];
  rules?: string[];
  sections?: string[];
  selection_mode?: string;
  binding?: string;
  data_source?: string;
  trigger_action?: string;
  reference_sources?: Record<string, string>;
}

export interface PageRegistryItem {
  pageId: string;
  title: string;
  pageType: string;
  template: string;
  useCaseRef?: string;
  binds?: Record<string, string>;
  sections?: PageRegistrySection[];
  actions?: string[];
}

export interface TabItem {
  id: string;
  pageId: string;
  title: string;
}

export interface OptionItem {
  id: number;
  [key: string]: string | number;
}

export interface ReferenceData {
  products: OptionItem[];
  customers: OptionItem[];
  departments: OptionItem[];
  employees: OptionItem[];
}

export interface ContractSummary {
  id: number;
  contractNo: string;
  contractName: string;
  status: string;
  signDate: string;
  totalAmount: number;
  purchaseAmount: number;
  taxRate: number;
  invoicedAmountTotal: number;
  receivedAmountTotal: number;
  invoiceStatus: string;
  receiptStatus: string;
  productName: string;
  productType: string;
  customerName: string;
  deptName: string;
  ownerName: string;
}

export interface PaymentTerm {
  stageNo: string;
  stageName: string;
  ratio: number;
}

export interface InvoiceRecord {
  id: number;
  invoiceNo: string;
  contractId: number;
  contractNo?: string;
  contractName?: string;
  customerName?: string;
  amount: number;
  taxRate: number;
  invoiceDate: string;
  status: string;
  isReceived: number | boolean;
  receivedDate?: string | null;
  stageMappings?: { stageNo: string; stageName?: string }[];
}

export interface ContractDetail extends ContractSummary {
  productNo: string;
  customerNo: string;
  deptNo: string;
  ownerNo: string;
  paymentTerms: PaymentTerm[];
  invoices: InvoiceRecord[];
}

export interface AIRenderTable {
  type: 'table';
  title?: string;
  headers: string[];
  rows: Array<Array<string | number>>;
}

export interface AIRenderChart {
  type: 'chart';
  title?: string;
  option: Record<string, unknown>;
  table?: {
    headers: string[];
    rows: Array<Array<string | number>>;
  };
}

export type AIRenderPayload = AIRenderTable | AIRenderChart;

export interface AIAssistantPayload {
  message: string;
  render?: AIRenderPayload | null;
  action?: { type: 'OPEN_PAGE'; pageId: string } | null;
}
