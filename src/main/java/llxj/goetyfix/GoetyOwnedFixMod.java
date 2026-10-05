package llxj.goetyfix;

import net.neoforged.fml.common.Mod;

/**
 * Goety isAlliedTo Null Guard Fix - 1.21.1 / NeoForge build.
 *
 * Fixes the recurring "Ticking entity" NullPointerException family caused by
 * Goety's isAlliedTo overrides receiving a null entity from
 * HurtByTargetGoal.alertOthers (which forwards a cleared or absent
 * getLastHurtByMob() into isAlliedTo without a null check).
 *
 * 1.20.1 lineage: this patch started as a Forge 1.20.1 mod that null-guarded
 * Goety's SRG method m_7307_ in 19 overriding classes plus vanilla Entity.
 * NeoForge 1.21.1 runs on Mojang official names, so the same 19 classes are
 * guarded through the plain `isAlliedTo` name here.
 *
 * Every guard returns false for a null argument, which is safe and correct:
 * a null entity can never be an ally. Non-null arguments pass through
 * unchanged, so no normal game behavior is altered.
 *
 * Mixin-only: contains no Goety code.
 */
@Mod("goetyownedfix")
public class GoetyOwnedFixMod {

    public GoetyOwnedFixMod() {
    }
}
