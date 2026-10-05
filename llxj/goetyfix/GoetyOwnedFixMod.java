package llxj.goetyfix;

import net.minecraftforge.fml.common.Mod;

/**
 * Goety Owned/Allies Null Guard Fix (v1.1.2)
 *
 * Fixes the recurring "Ticking entity" NullPointerException family caused by
 * Goety's isAlliedTo overrides receiving a null entity from
 * HurtByTargetGoal.alertOthers (which forwards a cleared/absent
 * getLastHurtByMob() into isAlliedTo without a null check).
 *
 * v1.0 fixed only Owned.isAlliedTo (Owned.java:186). v1.1 additionally
 * null-guards every Goety entity class that overrides isAlliedTo
 * (Apostle.java:399 included - it dereferences the argument via getType()
 * before reaching vanilla) plus the vanilla Entity.isAlliedTo entry point
 * as a safety net for pass-through callers.
 *
 * All guards return false for a null argument, which is safe and correct:
 * a null entity can never be an ally. Non-null arguments pass through
 * unchanged, so no normal game behavior is altered.
 *
 * v1.1.2: modId is "goetyownedfix" (previously "goetyfix"), so this mod can
 * be installed together with the unrelated "Goety Fix" memory-leak mod,
 * which also uses the modId "goetyfix". The mixin config was renamed to
 * mixins.goetyownedfix.json for the same reason.
 *
 * The actual fixes live in the mixins under llxj.goetyfix.mixin
 */
@Mod("goetyownedfix")
public class GoetyOwnedFixMod {

    public GoetyOwnedFixMod() {
    }
}
