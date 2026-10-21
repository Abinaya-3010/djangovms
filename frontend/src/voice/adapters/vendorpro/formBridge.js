/**
 * Form bridge (Option A). Plain JS, no React.
 *
 * A page registers a controller for a form it owns; the voice adapter looks it
 * up by name. The controller is the ONLY way voice actions touch page state.
 *
 * Controller contract:
 *   getState(): { open: boolean, mode: 'add' | 'edit' | null, blockedBy: string | null }
 *   openAdd():  { opened: boolean, reason?: 'already-open' | 'edit-in-progress' | 'blocked' }
 *
 * Mode matters: openAdd() must NEVER reset or overwrite a form that is already
 * open (Add or Edit). It only opens when the modal is fully closed.
 * Milestone 2 will extend this contract (setField, getValues, submit); not now.
 */
export const VENDOR_FORM = 'vendors.vendorForm';

const controllers = new Map();

/** Register a controller. Returns an unregister function that only removes THIS controller. */
export function registerFormController(name, controller) {
  controllers.set(name, controller);
  return () => {
    if (controllers.get(name) === controller) controllers.delete(name);
  };
}

export function getFormController(name) {
  return controllers.get(name) || null;
}
