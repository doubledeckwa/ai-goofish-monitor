// Based on the data structure from web_server.py and scraper.py

export interface ProductInfo {
  "Product title": string;
  "Current selling price": string;
  "Product original price"?: string;
  want_number_of_people?: string | number;
  "Product tag"?: string[];
  "Shipping area"?: string;
  "Seller nickname"?: string;
  "Product link": string;
  "Release time"?: string;
  "commodityID": string;
  "Product picture list"?: string[];
  "Product main image link"?: string;
  "Views"?: string | number;
}

export interface SellerInfo {
  "Seller nickname"?: string;
  "Seller avatar link"?: string;
  "Seller's personalized signature"?: string;
  "Seller is selling/Number of items sold"?: string;
  "The total number of reviews the seller has received"?: string;
  "Seller credit rating"?: string;
  "Buyer credit rating"?: string;
  "Seller Sesame Credit"?: string;
  "Seller registration time"?: string;
  "Number of positive reviews as a seller"?: string;
  "Positive rating as a seller"?: string;
  "Number of positive reviews as a buyer"?: string;
  "Positive rating as a buyer"?: string;
  "Product list posted by seller"?: any[]; // Define more strictly if needed
  "List of reviews received by the seller"?: any[]; // Define more strictly if needed
}

export interface AiAnalysis {
  is_recommended: boolean;
  reason: string;
  prompt_version?: string;
  risk_tags?: string[];
  criteria_analysis?: Record<string, any>;
  error?: string;
}

export interface ResultItem {
  "Crawl time": string;
  "Search keywords": string;
  "Task name": string;
  "Product information": ProductInfo;
  "Seller information": SellerInfo;
  ai_analysis: AiAnalysis;
}
