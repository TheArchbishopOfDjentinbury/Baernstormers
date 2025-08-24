
export type Metrics = {
  coffeeSpend: number;
  healthyFoodSpend: number;
  unhealthyFoodSpend: number;
  publictransportSpend: number;
  fuelSpend: number;
  transportSpend: number;
  swissMadeSpend: number;      // now CHF spent, not item count
  nonswissMadeSpend: number;   // likewise
  mediaSubscription: number;
  totalSpend: number;          // change from totalItemCount to totalSpend
  alcoholSpend: number;
  alcoholMonthlyLimit: number;
  consecutiveMonthsUnderBudget: number;
};

export type SpendRow = {
  category?: string;
  monthISO: string;
  amount?: string;   // e.g., "CHF 120.50"
};
