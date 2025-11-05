/**
 * Custom UI Component Registry
 *
 * Register all custom UI components that can be rendered by the agent.
 * Component names must match the names used in push_ui_message() calls.
 */

import HelloCard from './HelloCard';
import ScreenshotCard from './ScreenshotCard';

export const customComponents = {
  hello_card: HelloCard,
  screenshot_card: ScreenshotCard,
};

export type CustomComponentName = keyof typeof customComponents;
