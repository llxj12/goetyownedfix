package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Safety net on vanilla Entity.isAlliedTo(Entity) - the 1.21.1 entry point.
 *
 * Vanilla still dereferences its argument (the team lookup) with no null check.
 * Every Goety override that simply forwards a null argument to super would crash
 * here, as would any other mod doing the same. Guarding the vanilla entry point
 * covers all pass-through callers at once.
 *
 * A null entity can never be an ally, so false is safe and correct; non-null
 * arguments are untouched. Entity.isAlliedTo(Team) is a different method and is
 * deliberately not touched.
 */
@Mixin(Entity.class)
public class EntityAlliedGuardMixin {

    @Inject(method = "isAlliedTo", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
