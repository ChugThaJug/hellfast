// Simple SVG icons as string templates
export const icons = {
  search: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-search"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`,
  
  check: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-check"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  
  loading: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-loading animate-spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>`
}

// Component to render an icon
export function Icon({ name, className = "" }) {
  // Get the icon by name
  const iconSvg = icons[name] || "";
  
  // Create the SVG node
  if (typeof document !== 'undefined') {
    const div = document.createElement('div');
    div.innerHTML = iconSvg;
    const svg = div.firstChild;
    
    // Add any classes
    if (className && svg) {
      svg.classList.add(...className.split(' '));
    }
    
    return svg;
  }
  
  return null;
}