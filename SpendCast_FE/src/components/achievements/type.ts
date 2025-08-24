export type Metrics = {
  coffeeSpend: number;
  healthyFoodSpend: number;
  unhealthyFoodSpend: number;
  publictransportSpend: number;
  fuelSpend: number;
  transportSpend: number;
  swissMadeSpend: number;
  nonswissMadeSpend: number;
  mediaSubscription: number;
  totalSpend: number;
  alcoholSpend: number;
  alcoholMonthlyLimit: number;
  consecutiveMonthsUnderBudget: number;
};

export type SpendRow = {
  category?: string;
  monthISO: string;
  amount?: string;
};
