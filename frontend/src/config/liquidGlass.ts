export interface LiquidGlassConfig {
  displacementScale: number
  blurAmount: number
  saturation: number
  aberrationIntensity: number
  elasticity: number
  cornerRadius: number
  padding: string
}

// Central configuration for all liquid glass components
// These values are more subtle and refined than the original intense settings
export const LIQUID_GLASS_CONFIG: LiquidGlassConfig = {
  // Small but visible displacement for subtle glass effect
  displacementScale: 5,
  
  // Reduced from 0.05 to 0.02 - minimal blur for clarity
  blurAmount: 0.05,
  
  // Reduced from 120 to 110 - subtle saturation boost
  saturation: 120,
  
  // Reduced from 4 to 2 - gentler chromatic aberration
  aberrationIntensity: 4,
  
  // Reduced from 0.05 to 0.03 - more controlled elastic movement
  elasticity: 0.03,
  
  // Keep the same corner radius for consistency
  cornerRadius: 16,
  
  // Standard padding
  padding: "24px 32px"
}

// Export individual values for convenience
export const {
  displacementScale,
  blurAmount,
  saturation,
  aberrationIntensity,
  elasticity,
  cornerRadius,
  padding
} = LIQUID_GLASS_CONFIG 