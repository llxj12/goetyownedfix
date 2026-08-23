package llxj.goetyfix.mixin;

import com.Polarice3.Goety.utils.MobUtil;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Null-guard for the static helper MobUtil.illagerAllies(Entity, Entity).
 *
 * The helper dereferences its arguments (getTeam()) without a null check, so
 * a null argument NPEs inside the utility. Several Goety isAlliedTo overrides
 * route through it; the per-class isAlliedTo guards already stop null from
 * reaching it, but this closes the helper itself for any other callers.
 *
 * Returning false when either argument is null is safe and correct: a null
 * entity can never be an ally.
 */
@Mixin(MobUtil.class)
public class MobUtilNullGuardMixin {

    @Inject(method = "illagerAllies", at = @At("HEAD"), cancellable = true)
    private static void goetyfix$nullGuardIllagerAllies(Entity self, Entity other, CallbackInfoReturnable<Boolean> cir) {
        if (self == null || other == null) {
            cir.setReturnValue(false);
        }
    }
}
