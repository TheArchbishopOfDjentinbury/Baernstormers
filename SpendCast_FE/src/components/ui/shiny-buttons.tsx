import React from 'react';

type Props = {
  ledColor: string;
  size?: number;
  children: React.ReactNode;
};

export function ShinyLedFrame({ ledColor, size = 96, children }: Props) {
  const px = `${size}px`;
  const ringThickness = 8;

  return (
    <div
      className={[
        'relative rounded-full isolate',
        'transition-transform duration-300',
        'hover:scale-[1.04] active:scale-95',
        'focus-visible:outline-none focus-visible:ring-2',
        'focus-visible:ring-white/70 focus-visible:ring-offset-2',
        'focus-visible:ring-offset-black/10',
      ].join(' ')}
      style={
        {
          '--led': ledColor,
          width: px,
          height: px,
          padding: `${ringThickness}px`,
          filter: 'drop-shadow(0 4px 14px rgba(0,0,0,.25))',
        } as React.CSSProperties
      }
      role="img"
      aria-label="Achievement button"
    >
      <div
        className={[
          'pointer-events-none absolute inset-0 rounded-full',
          "before:content-[''] before:absolute before:inset-0 before:rounded-full",
          'before:bg-[conic-gradient(from_0deg,var(--led)_0_15%,transparent_15%_100%)]',
          'before:[mask:radial-gradient(farthest-side,transparent_calc(100%-8px),#000_calc(100%-8px))]',
          'before:animate-[spin_8s_linear_infinite]',
          'shadow-[0_0_0_1px_var(--led),0_0_18px_3px_var(--led)/55%]',
        ].join(' ')}
        aria-hidden
      />

      <div
        className={[
          'relative rounded-full overflow-hidden bg-white',
          'border-2 border-white',
          'shadow-[inset_0_1px_0_rgba(255,255,255,.9),inset_0_-10px_24px_rgba(0,0,0,.12),0_10px_22px_rgba(0,0,0,.12)]',
        ].join(' ')}
      >
        <div
          className="pointer-events-none absolute inset-0 rounded-full"
          style={{
            background:
              'radial-gradient(120% 80% at 50% -10%, rgba(255,255,255,.9) 0%, rgba(255,255,255,.5) 35%, transparent 60%)',
          }}
          aria-hidden
        />
        <div
          className="pointer-events-none absolute inset-0 rounded-full mix-blend-screen opacity-30 animate-[spin_12s_linear_infinite]"
          style={{
            background:
              'conic-gradient(from 0deg, rgba(255,255,255,.0) 0 60%, rgba(255,255,255,.6) 75%, rgba(255,255,255,.0) 100%)',
          }}
          aria-hidden
        />
        <div className="relative z-10 w-full h-full grid place-items-center">
          <div className="w-20 h-20 rounded-full flex items-center justify-center ">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
