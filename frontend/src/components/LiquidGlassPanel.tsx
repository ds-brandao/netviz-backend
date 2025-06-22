import React, { forwardRef, useState, useEffect, useCallback, useRef } from 'react';
import { 
  GlassContainer, 
  type LiquidGlassProps 
} from './SimpleLiquidGlass/SimpleLiquidGlass';

export const LiquidGlassPanel = forwardRef<HTMLDivElement, LiquidGlassProps>(({
  children,
  displacementScale = 100,
  blurAmount = 0.05,
  saturation = 120,
  aberrationIntensity = 4,
  elasticity = 0.05,
  cornerRadius = 16,
  globalMousePos: externalGlobalMousePos,
  mouseOffset: externalMouseOffset,
  mouseContainer = null,
  className = "",
  padding = "24px 32px",
  overLight = false,
  style = {},
  mode = "standard",
  onClick,
}, ref) => {
  const glassRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [glassSize, setGlassSize] = useState({ width: 270, height: 69 });
  const [internalGlobalMousePos, setInternalGlobalMousePos] = useState({ x: 0, y: 0 });
  const [internalMouseOffset, setInternalMouseOffset] = useState({ x: 0, y: 0 });

  // Use external mouse position if provided, otherwise use internal
  const globalMousePos = externalGlobalMousePos || internalGlobalMousePos;
  const mouseOffset = externalMouseOffset || internalMouseOffset;

  // Internal mouse tracking
  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      const container = mouseContainer?.current || glassRef.current;
      if (!container) {
        return;
      }

      const rect = container.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      setInternalMouseOffset({
        x: ((e.clientX - centerX) / rect.width) * 100,
        y: ((e.clientY - centerY) / rect.height) * 100,
      });

      setInternalGlobalMousePos({
        x: e.clientX,
        y: e.clientY,
      });
    },
    [mouseContainer],
  );

  // Set up mouse tracking if no external mouse position is provided
  useEffect(() => {
    if (externalGlobalMousePos && externalMouseOffset) {
      // External mouse tracking is provided, don't set up internal tracking
      return;
    }

    const container = mouseContainer?.current || glassRef.current;
    if (!container) {
      return;
    }

    container.addEventListener("mousemove", handleMouseMove);

    return () => {
      container.removeEventListener("mousemove", handleMouseMove);
    };
  }, [handleMouseMove, mouseContainer, externalGlobalMousePos, externalMouseOffset]);

  // Calculate directional scaling based on mouse position
  const calculateDirectionalScale = useCallback(() => {
    if (!globalMousePos.x || !globalMousePos.y || !glassRef.current) {
      return "scale(1)";
    }

    const rect = glassRef.current.getBoundingClientRect();
    const pillCenterX = rect.left + rect.width / 2;
    const pillCenterY = rect.top + rect.height / 2;
    const pillWidth = glassSize.width;
    const pillHeight = glassSize.height;

    const deltaX = globalMousePos.x - pillCenterX;
    const deltaY = globalMousePos.y - pillCenterY;

    // Calculate distance from mouse to pill edges (not center)
    const edgeDistanceX = Math.max(0, Math.abs(deltaX) - pillWidth / 2);
    const edgeDistanceY = Math.max(0, Math.abs(deltaY) - pillHeight / 2);
    const edgeDistance = Math.sqrt(edgeDistanceX * edgeDistanceX + edgeDistanceY * edgeDistanceY);

    // Activation zone: 200px from edges
    const activationZone = 200;

    // If outside activation zone, no effect
    if (edgeDistance > activationZone) {
      return "scale(1)";
    }

    // Calculate fade-in factor (1 at edge, 0 at activation zone boundary)
    const fadeInFactor = 1 - edgeDistance / activationZone;

    // Normalize the deltas for direction
    const centerDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    if (centerDistance === 0) {
      return "scale(1)";
    }

    const normalizedX = deltaX / centerDistance;
    const normalizedY = deltaY / centerDistance;

    // Calculate stretch factors with fade-in
    const stretchIntensity = Math.min(centerDistance / 300, 1) * elasticity * fadeInFactor;

    // X-axis scaling: stretch horizontally when moving left/right, compress when moving up/down
    const scaleX = 1 + Math.abs(normalizedX) * stretchIntensity * 0.3 - Math.abs(normalizedY) * stretchIntensity * 0.15;

    // Y-axis scaling: stretch vertically when moving up/down, compress when moving left/right
    const scaleY = 1 + Math.abs(normalizedY) * stretchIntensity * 0.3 - Math.abs(normalizedX) * stretchIntensity * 0.15;

    return `scaleX(${Math.max(0.8, scaleX)}) scaleY(${Math.max(0.8, scaleY)})`;
  }, [globalMousePos, elasticity, glassSize]);

  // Helper function to calculate fade-in factor based on distance from element edges
  const calculateFadeInFactor = useCallback(() => {
    if (!globalMousePos.x || !globalMousePos.y || !glassRef.current) {
      return 0;
    }

    const rect = glassRef.current.getBoundingClientRect();
    const pillCenterX = rect.left + rect.width / 2;
    const pillCenterY = rect.top + rect.height / 2;
    const pillWidth = glassSize.width;
    const pillHeight = glassSize.height;

    const edgeDistanceX = Math.max(0, Math.abs(globalMousePos.x - pillCenterX) - pillWidth / 2);
    const edgeDistanceY = Math.max(0, Math.abs(globalMousePos.y - pillCenterY) - pillHeight / 2);
    const edgeDistance = Math.sqrt(edgeDistanceX * edgeDistanceX + edgeDistanceY * edgeDistanceY);

    const activationZone = 200;
    return edgeDistance > activationZone ? 0 : 1 - edgeDistance / activationZone;
  }, [globalMousePos, glassSize]);

  // Helper function to calculate elastic translation
  const calculateElasticTranslation = useCallback(() => {
    if (!glassRef.current) {
      return { x: 0, y: 0 };
    }

    const fadeInFactor = calculateFadeInFactor();
    const rect = glassRef.current.getBoundingClientRect();
    const pillCenterX = rect.left + rect.width / 2;
    const pillCenterY = rect.top + rect.height / 2;

    return {
      x: (globalMousePos.x - pillCenterX) * elasticity * 0.1 * fadeInFactor,
      y: (globalMousePos.y - pillCenterY) * elasticity * 0.1 * fadeInFactor,
    };
  }, [globalMousePos, elasticity, calculateFadeInFactor]);

  // Update glass size whenever component mounts or window resizes
  useEffect(() => {
    const updateGlassSize = () => {
      if (glassRef.current) {
        const rect = glassRef.current.getBoundingClientRect();
        setGlassSize({ width: rect.width, height: rect.height });
      }
    };

    updateGlassSize();
    window.addEventListener("resize", updateGlassSize);
    return () => window.removeEventListener("resize", updateGlassSize);
  }, []);

  // Also update glass size when children change (for dynamic content)
  useEffect(() => {
    const updateGlassSize = () => {
      if (glassRef.current) {
        const rect = glassRef.current.getBoundingClientRect();
        setGlassSize({ width: rect.width, height: rect.height });
      }
    };

    // Use ResizeObserver if available for better performance
    if (typeof ResizeObserver !== 'undefined' && glassRef.current) {
      const observer = new ResizeObserver(updateGlassSize);
      observer.observe(glassRef.current);
      return () => observer.disconnect();
    } else {
      // Fallback to mutation observer
      const observer = new MutationObserver(updateGlassSize);
      if (glassRef.current) {
        observer.observe(glassRef.current, { childList: true, subtree: true });
      }
      return () => observer.disconnect();
    }
  }, [children]);

  const elasticTranslation = calculateElasticTranslation();
  const directionalScale = calculateDirectionalScale();
  
  const transformStyle = `translate(${elasticTranslation.x}px, ${elasticTranslation.y}px) ${isActive && onClick ? "scale(0.96)" : directionalScale}`;

  const baseStyle = {
    ...style,
    transform: transformStyle,
    transition: "all ease-out 0.2s",
  };

  return (
    <div ref={ref} className={`relative ${className}`} style={baseStyle}>
      {/* Over light effect */}
      <div
        className={`bg-black transition-all duration-150 ease-in-out pointer-events-none ${overLight ? "opacity-20" : "opacity-0"}`}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: glassSize.height,
          width: glassSize.width,
          borderRadius: `${cornerRadius}px`,
          transition: baseStyle.transition,
        }}
      />
      <div
        className={`bg-black transition-all duration-150 ease-in-out pointer-events-none mix-blend-overlay ${overLight ? "opacity-100" : "opacity-0"}`}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: glassSize.height,
          width: glassSize.width,
          borderRadius: `${cornerRadius}px`,
          transition: baseStyle.transition,
        }}
      />

      <GlassContainer
        ref={glassRef}
        className=""
        style={{}}
        cornerRadius={cornerRadius}
        displacementScale={overLight ? displacementScale * 0.5 : displacementScale}
        blurAmount={blurAmount}
        saturation={saturation}
        aberrationIntensity={aberrationIntensity}
        glassSize={glassSize}
        padding={padding}
        mouseOffset={mouseOffset}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onMouseDown={() => setIsActive(true)}
        onMouseUp={() => setIsActive(false)}
        active={isActive}
        overLight={overLight}
        onClick={onClick}
        mode={mode}
      >
        {children}
      </GlassContainer>

      {/* Border layer 1 - extracted from glass container */}
      <span
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: glassSize.height,
          width: glassSize.width,
          borderRadius: `${cornerRadius}px`,
          transition: baseStyle.transition,
          pointerEvents: "none",
          mixBlendMode: "screen",
          opacity: 0.2,
          padding: "1.5px",
          WebkitMask: "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
          boxShadow: "0 0 0 0.5px rgba(255, 255, 255, 0.5) inset, 0 1px 3px rgba(255, 255, 255, 0.25) inset, 0 1px 4px rgba(0, 0, 0, 0.35)",
          background: `linear-gradient(
            ${135 + mouseOffset.x * 1.2}deg,
            rgba(255, 255, 255, 0.0) 0%,
            rgba(255, 255, 255, ${0.12 + Math.abs(mouseOffset.x) * 0.008}) ${Math.max(10, 33 + mouseOffset.y * 0.3)}%,
            rgba(255, 255, 255, ${0.4 + Math.abs(mouseOffset.x) * 0.012}) ${Math.min(90, 66 + mouseOffset.y * 0.4)}%,
            rgba(255, 255, 255, 0.0) 100%
          )`,
        }}
      />

      {/* Border layer 2 - duplicate with mix-blend-overlay */}
      <span
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: glassSize.height,
          width: glassSize.width,
          borderRadius: `${cornerRadius}px`,
          transition: baseStyle.transition,
          pointerEvents: "none",
          mixBlendMode: "overlay",
          padding: "1.5px",
          WebkitMask: "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
          boxShadow: "0 0 0 0.5px rgba(255, 255, 255, 0.5) inset, 0 1px 3px rgba(255, 255, 255, 0.25) inset, 0 1px 4px rgba(0, 0, 0, 0.35)",
          background: `linear-gradient(
            ${135 + mouseOffset.x * 1.2}deg,
            rgba(255, 255, 255, 0.0) 0%,
            rgba(255, 255, 255, ${0.32 + Math.abs(mouseOffset.x) * 0.008}) ${Math.max(10, 33 + mouseOffset.y * 0.3)}%,
            rgba(255, 255, 255, ${0.6 + Math.abs(mouseOffset.x) * 0.012}) ${Math.min(90, 66 + mouseOffset.y * 0.4)}%,
            rgba(255, 255, 255, 0.0) 100%
          )`,
        }}
      />

      {/* Hover effects */}
      {onClick && (
        <>
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              height: glassSize.height,
              width: glassSize.width + 1,
              borderRadius: `${cornerRadius}px`,
              pointerEvents: "none",
              transition: "all 0.2s ease-out",
              opacity: isHovered || isActive ? 0.5 : 0,
              backgroundImage: "radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0) 50%)",
              mixBlendMode: "overlay",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              height: glassSize.height,
              width: glassSize.width + 1,
              borderRadius: `${cornerRadius}px`,
              pointerEvents: "none",
              transition: "all 0.2s ease-out",
              opacity: isActive ? 0.5 : 0,
              backgroundImage: "radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0) 80%)",
              mixBlendMode: "overlay",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              height: glassSize.height,
              width: glassSize.width + 1,
              borderRadius: `${cornerRadius}px`,
              pointerEvents: "none",
              transition: "all 0.2s ease-out",
              opacity: isHovered ? 0.4 : isActive ? 0.8 : 0,
              backgroundImage: "radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0) 100%)",
              mixBlendMode: "overlay",
            }}
          />
        </>
      )}
    </div>
  );
});

LiquidGlassPanel.displayName = "LiquidGlassPanel";
